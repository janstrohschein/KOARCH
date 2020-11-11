import psycopg2

from classes.CKafkaPC import KafkaPC


class PostgresPC(KafkaPC):
    def __init__(self, config_path=None, config_section=None):
        super().__init__(config_path, config_section)
        self.create_connection()

    def create_connection(self):
        self.db_host = self.config["POSTGRES"]["host"]
        self.db = self.config["POSTGRES"]["database"]
        self.db_user = self.config["POSTGRES"]["user"]
        self.db_password = self.config["POSTGRES"]["password"]
        self.port = self.config["POSTGRES"]["port"]
        self.conn = psycopg2.connect(
            host=self.db_host,
            port=self.port,
            database=self.db,
            user=self.db_user,
            password=self.db_password,
        )
        self.conn.autocommit = True
        self.cur = self.conn.cursor()

    def execute_statement(self, sql_statement, values=None):
        if values is None:
            self.cur.execute(sql_statement)
        else:
            self.cur.execute(sql_statement, values)
