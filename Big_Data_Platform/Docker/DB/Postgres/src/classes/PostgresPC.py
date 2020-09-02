import psycopg2

from classes.KafkaPC import KafkaPC


class PostgresPC(KafkaPC):
    def __init__(self, config_path=None, config_section=None):
        super().__init__(config_path, config_section)
        self.db_host = self.config['POSTGRES']['host']
        self.db = self.config['POSTGRES']['database']
        self.db_user = self.config['POSTGRES']['user']
        self.db_password = self.config['POSTGRES']['password']
        self.port = self.config['POSTGRES']['port']
        self.conn = psycopg2.connect(host=self.db_host, port=self.port, database=self.db, user=self.db_user,
                                     password=self.db_password)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
