import sqlite3
import threading


class Database:
    def __init__(self, db_name):
        self.connection = sqlite3.connect('data/' + db_name, check_same_thread=False)
        self.db = self.connection.cursor()
        self.lock = threading.Lock()

    def execute(self, command, bindings=(), commit=False):
        try:
            with self.lock:
                self.db.execute(command, bindings)
                if commit:
                    self.connection.commit()
            return True
        except (sqlite3.OperationalError,sqlite3.ProgrammingError) as e:
            print('SQL Error: {}'.format(e))
            print('Command Used: {}'.format(command))
            if bindings:
                print('Bindings: {}'.format(bindings))
            return e

    def create_table(self, table_name, table_entries, overwrite=False):
        header_type_list = list()
        if overwrite:
            self.execute('DROP TABLE IF EXISTS {}'.format(table_name))
        command = 'CREATE TABLE IF NOT EXISTS {} ('.format(table_name)
        for k in table_entries:
            header_type_list.append('{} {}'.format(k[0], k[1]))
        command += ', '.join(header_type_list) + ');'
        return self.execute(command, commit=True)

    def insert(self, table_name, values):
        command = 'INSERT INTO {} VALUES({});'.format(
            table_name,
            ','.join(list('?' * len(values)))
        )
        return self.execute(command, bindings=values, commit=True)

    def delete(self, table_name, conditions):
        where = list()
        bindings = list()
        command = 'DELETE FROM {}'.format(table_name)
        if conditions:
            command += ' WHERE '
            for k in conditions:
                where.append(k[0])
                if k[1]:
                    where[-1] += '=?'
                    bindings.append(k[1])
            command += ' AND '.join(where) + ';'
        return self.execute(command, bindings=bindings, commit=True)

    def select(self, headers, table_name, conditions=None, return_value=False, single_return=False):
        bindings = list()
        where = list()
        if type(headers) is list:
            headers = ','.join(headers)
        if type(table_name) is list:
            table_name = ','.join(table_name)
        command = 'SELECT {} FROM {}'.format(headers, table_name)
        if conditions:
            command += ' WHERE '
            for k in conditions:
                where.append(k[0])
                if k[1]:
                    where[-1] += '=?'
                    bindings.append(k[1])
            command += ' AND '.join(where) + ';'
        if return_value:
            self.execute(command, bindings=bindings)
            return self.return_selection(single_return=single_return)
        else:
            return self.execute(command, bindings=bindings)

    def return_selection(self, single_return=False):
        return_list = list()
        for i in self.db:
            return_list.append(i)
        if single_return:
            if len(return_list) == 1:
                return return_list[0]
            else:
                return None
        else:
            return return_list
