import sqlite3


class Database:
    def __init__(self, dbname):
        path = 'data/' + dbname
        self.db = sqlite3.connect(path, check_same_thread=False).cursor()

    def execute(self, command):
        try:
            self.db.execute(command)
            return True
        except sqlite3.OperationalError as e:
            print('SQL Error: {}'.format(e))
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
