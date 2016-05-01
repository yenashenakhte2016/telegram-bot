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
