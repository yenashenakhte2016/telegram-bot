import collections
import logging
import sqlite3
import threading


class Database:
    def __init__(self, db_name):
        self.log = logging.getLogger(__name__)
        self.connection = sqlite3.connect('data/' + db_name, check_same_thread=False)
        self.db = self.connection.cursor()
        self.lock = threading.Lock()

    def execute(self, command, bindings=list(), commit=False):
        try:
            with self.lock:
                self.db.execute(command, bindings)
            if commit:
                self.connection.commit()
            return True
        except (sqlite3.OperationalError,sqlite3.ProgrammingError) as e:
            self.log.ERROR("SQL ERROR: {}\nCOMMAND: {}\nBINDINGS:".format(e, command, bindings))
            return e

    def create_table(self, table_name, parameters, drop_existing=True):
        if drop_existing:
            self.execute('DROP TABLE IF EXISTS {}'.format(table_name))
        query = "CREATE TABLE IF NOT EXISTS {}(".format(table_name)
        parameters = collections.OrderedDict(parameters)
        for column, data_type in parameters.items():
            query += '\n{} {}'.format(column, data_type)
        query += '\n);'
        return self.execute(query, commit=True)

    def insert(self, table_name, values):
        values = collections.OrderedDict(values)
        query = "INSERT INTO {} ({}) VALUES({});".format(
            table_name,
            ', '.join(values.keys()),
            ','.join(list('?' * len(values.items())))
        )
        return self.execute(query, bindings=values.values(), commit=True)

    def delete(self, table_name, conditions):
        conditions = collections.OrderedDict(conditions)
        query = "DELETE FROM {}\nWHERE ".format(table_name)
        for column in conditions.keys():
            query += " {}".format(column)
            if conditions[column]:
                query += "=?"
        query += ";"
        return self.execute(query, conditions.values(), commit=True)

    def select(self, table_name, columns, conditions):
        conditions = collections.OrderedDict(conditions)
        query = "SELECT {} FROM {} WHERE".format(', '.join(columns), table_name)
        for column in conditions.keys():
            query += " {}".format(column)
            if conditions[column]:
                query += "=?"
        query += ";"
        return self.execute(query, conditions.values())
