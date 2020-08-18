import psycopg2

from classes.KafkaPC import KafkaPC

class PostgresPC(KafkaPC):
    def __init__(self, config_path=None, in_topic=None, in_group=None, in_schema_file=None, out_topic=None, out_schema_file=None):
        super().__init__(config_path, in_topic, in_group, in_schema_file, out_topic, out_schema_file)

        self.db_host = str(*self.config['postgres']['host'])
        print('Host:', self.db_host)
        self.db = str(*self.config['postgres']['database'])
        self.db_user = str(*self.config['postgres']['user'])
        self.db_password = str(*self.config['postgres']['password'])
        self.port = int(*self.config['postgres']['port'])
        print(self.port)
        self.conn = psycopg2.connect(host=self.db_host, port=self.port, database=self.db, user=self.db_user, password=self.db_password)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        print('PostgreSQL database version:')
        print(self.cur.execute('SELECT version()'))
