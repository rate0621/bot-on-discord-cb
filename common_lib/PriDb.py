import sqlite3

class PriDb():
    def __init__(self):
        self.dbname = "/var/local/discord_pri.db"

    def create_server_table(self, server_name):
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()

        query = 'CREATE TABLE IF NOT EXISTS discord_%s_users(user_id integer, user_name text, join_at text)' % server_name
        c.execute(query)

        query = 'CREATE UNIQUE INDEX IF NOT EXISTS idx_user_id ON discord_%s_users(user_id)' % server_name
        c.execute(query)

        query = 'CREATE TABLE IF NOT EXISTS discord_%s_talks(user_id integer, text text, talk_at text)' % server_name
        c.execute(query)

        conn.commit()

    def insert_member(self, server_name, user_id, user_name, join_date):
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()

        query = 'INSERT OR REPLACE INTO discord_%s_users (user_id, user_name, join_at) VALUES (?,?,?)' % server_name
        user = (user_id, user_name, join_date)
        c.execute(query, user)

        conn.commit()

    def insert_talk(self, server_name, user_id, text, talk_at):
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()

        query = 'INSERT INTO discord_%s_talks (user_id, text, talk_at) VALUES (?,?,?)' % server_name
        talk = (user_id, text, talk_at)
        c.execute(query, talk)

        conn.commit()


if __name__ == "__main__":
    PriDb().create_server_table(111)
    PriDb().insert_member(111, 1, 'bbb', '2018/12/14 08:11:53')
