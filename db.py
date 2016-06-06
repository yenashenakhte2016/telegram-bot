import collections
import sqlite3
import threading


class Database:
    def __init__(self, db_name):
        self.connection = sqlite3.connect('data/' + db_name)
        self.db = self.connection.cursor()
        self.execute_lock = threading.Lock()

    def execute(self, command, bindings=list(), commit=False):
        with self.execute_lock:
            self.db.execute(command, bindings)
            if commit:
                self.connection.commit()
            return True

    def create_table(self, table_name, parameters, drop_existing=False):
        if drop_existing:
            self.drop_table(table_name)
        query = "CREATE TABLE IF NOT EXISTS {}(".format(table_name)
        parameters = collections.OrderedDict(parameters)
        column_names = parameters.keys()
        column_types = parameters.values()
        query += ', '.join('\n{} {}'.format(*t) for t in zip(column_names, column_types)) + '\n);'
        return self.execute(query, commit=True)

    def drop_table(self, table_name):
        self.execute('DROP TABLE IF EXISTS {}'.format(table_name))

    def insert(self, table_name, values):
        values = collections.OrderedDict(values)
        query = "INSERT INTO {} ({}) VALUES({});".format(
            table_name,
            ', '.join(values.keys()),
            ','.join(list('?' * len(values.items())))
        )
        return self.execute(query, bindings=list(values.values()), commit=True)

    def update(self, table_name, values, conditions=None):
        values = collections.OrderedDict(values)
        bindings = list(values.values())
        condition_list = list()
        query = "UPDATE {}\nSET ".format(table_name)
        for column in values.keys():
            condition_list.append("{}=?".format(column))
        query += ' AND '.join(condition_list)
        if conditions:
            conditions = collections.OrderedDict(conditions)
            bindings += list(conditions.values())
            condition_list = list()
            query += "\nWHERE "
            for column in conditions.keys():
                condition_list.append("{}=?".format(column))
            query += ' AND '.join(condition_list)
        query += ';'
        return self.execute(query, bindings, commit=True)

    def delete(self, table_name, conditions):
        conditions = collections.OrderedDict(conditions)
        condition_list = list()
        query = "DELETE FROM {}\nWHERE ".format(table_name)
        for column in conditions.keys():
            condition_list.append("{}=?".format(column))
        query += ' AND '.join(condition_list) + ";"
        bindings = list(conditions.values())
        return self.execute(query, bindings, commit=True)

    def select(self, table_name, columns, conditions=None):
        return_obj = list()
        query = "SELECT {} FROM {}".format(', '.join(columns), table_name)
        if conditions:
            query += ' WHERE '
            conditions = collections.OrderedDict(conditions)
            condition_list = list()
            for column in conditions.keys():
                condition_list.append("{}=?".format(column))
            query += ' AND '.join(condition_list)
            bindings = list(conditions.values())
            self.execute(query, bindings)
        else:
            self.execute(query)
        results = self.db
        for index, result in enumerate(results):
            return_obj.append(dict())
            for i, column_name in enumerate(columns):
                column_name = column_name.replace('DISTINCT ', '')
                return_obj[index].update({column_name: result[i]})
        return return_obj
