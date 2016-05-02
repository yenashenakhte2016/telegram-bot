import sqlite3


class Database:
    def __init__(self, db_name):
        path = 'data/' + db_name
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.db = self.connection.cursor()

    def execute(self, command):
        try:
            self.connection.commit()
            self.db.execute(command)
            return True
        except sqlite3.OperationalError as e:
            print('SQL Error: {}'.format(e))
            print('Command Used: {}'.format(command))
            return e

    def create_table(self, table_name, table_entries, overwrite=False):
        header_type_list = list()
        if overwrite:
            self.db.execute('DROP TABLE IF EXISTS {}'.format(table_name))
        command = """CREATE TABLE IF NOT EXISTS {} (""".format(table_name)
        for k in table_entries:
            header_type_list.append('{} {}'.format(k[0], k[1]))
        command += ', '.join(header_type_list) + ');'
        return self.db.execute(command)

    def insert(self, table_name, values):
        if type(values) is list:
            for i, v in enumerate(values):
                if type(v) is int:
                    values[i] = str(v)
                else:
                    values[i] = '"{}"'.format(v)
            values = ','.join(values)
        return self.db.execute('INSERT INTO {} VALUES({});'.format(table_name, values))

    def delete(self, table_name, conditions):
        where = list()
        command = 'DELETE FROM {} WHERE '.format(table_name)
        for k in conditions:
            where.append('{}={}'.format(k[0], k[1]))
        command += ' AND '.join(where) + ';'
        return self.execute(command)

    def select(self, headers, table_name, conditions=None, return_value=False, single_return=False):
        where = list()
        if type(headers) is list:
            headers = ','.join(headers)
        if type(table_name) is list:
            table_name = ','.join(table_name)
        command = 'SELECT {} FROM {} '.format(headers, table_name)
        if conditions:
            command += 'WHERE '
            for k in conditions:
                if type(k[1]) is int:
                    where.append('{}={}'.format(k[0], k[1]))
                else:
                    where.append('{}="{}"'.format(k[0], k[1]))
            command += ' AND '.join(where) + ';'
        if return_value:
            self.execute(command)
            return self.return_selection(single_return=single_return)
        else:
            return self.execute(command)

    def return_selection(self, single_return=False):
        return_list = list()
        for i in self.db:
            return_list.append(i)
        if single_return:
            if len(return_list) == 1:
                return return_list[0]
            else:
                raise Exception('More than one return!')
        else:
            return return_list
