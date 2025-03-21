import datetime
import random
import time
from multiprocessing.pool import ThreadPool

import psycopg2
import yaml


class DBArgs(object):
    def __init__(self, dbtype, config, dbname=None):
        self.dbtype = dbtype
        if self.dbtype == "mysql":
            self.host = config["host"]
            self.port = config["port"]
            self.user = config["user"]
            self.password = config["password"]
            self.dbname = dbname if dbname else config["dbname"]
            self.driver = "com.mysql.jdbc.Driver"
            self.jdbc = "jdbc:mysql://"
        else:
            self.host = config["host"]
            self.port = config["port"]
            self.user = config["user"]
            self.password = config["password"]
            self.dbname = dbname if dbname else config["dbname"]
            self.driver = "org.postgresql.Driver"
            self.jdbc = "jdbc:postgresql://"


class Database:
    def __init__(self, args, timeout=-1):
        self.args = args
        self.conn = self.resetConn(timeout)

        # self.schema = self.compute_table_schema()

    def resetConn(self, timeout=-1):
        conn = psycopg2.connect(
            database=self.args.dbname,
            user=self.args.user,
            password=self.args.password,
            host=self.args.host,
            port=self.args.port,
        )
        return conn

    def execute_sqls(self, sql):
        self.conn = self.resetConn(timeout=-1)
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()
        cur.close()
        self.conn.close()

    def execute_sql_duration(self, duration, sql, max_id=0, commit_interval=500):
        self.conn = self.resetConn(timeout=-1)
        cursor = self.conn.cursor()
        start = time.time()
        cnt = 0
        if duration > 0:
            while (time.time() - start) < duration:
                if max_id > 0:
                    id = random.randint(1, max_id - 1)
                    cursor.execute(sql + str(id) + ";")
                else:
                    cursor.execute(sql)
                cnt += 1
                if cnt % commit_interval == 0:
                    self.conn.commit()
        else:
            print("error, the duration should be larger than 0")
        self.conn.commit()
        cursor.close()
        self.conn.close()
        return cnt

    def concurrent_execute_sql(
        self, threads, duration, sql, max_id=0, commit_interval=500
    ):
        pool = ThreadPool(threads)
        results = [
            pool.apply_async(
                self.execute_sql_duration, (duration, sql, max_id, commit_interval)
            )
            for _ in range(threads)
        ]
        pool.close()
        pool.join()
        return results


def init():
    # add the config
    config_path = "/root/DB-GPT/config/tool_config.yaml"
    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)
    db_args = DBArgs("pgsql", config)
    return db_args


# create a table
def create_table(table_name, colsize, ncolumns):
    db = Database(init())
    column_definitions = ", ".join(
        f"name{i} varchar({colsize})" for i in range(ncolumns)
    )
    creat_sql = (
        f"CREATE TABLE {table_name} (id int, {column_definitions}, time timestamp);"
    )
    db.execute_sqls(creat_sql)


# delete the table
def delete_table(table_name):
    db = Database(init())
    delete_sql = f"DROP TABLE if exists {table_name}"
    db.execute_sqls(delete_sql)


# print the current time
def print_time():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    print(formatted_time)


"""insert_large_data"""


def insert_large_data(threads, duration, ncolumns, nrows, colsize, table_name="table1"):
    print_time()
    # Delete undeleted tables
    delete_table(table_name)
    # create a new table
    create_table(table_name, colsize, ncolumns)
    db = Database(init())
    # insert the data
    # insert_definitions = ', '.join(f'repeat(round(random()*999)::text,{(colsize//3)})' for i in range(ncolumns))
    insert_definitions = ", ".join(
        f"(SELECT substr(md5(random()::text), 1, {colsize}))" for i in range(ncolumns)
    )
    insert_data = f"insert into {table_name} select generate_series(1,{nrows}),{insert_definitions}, now();"
    db.concurrent_execute_sql(threads, duration, insert_data, commit_interval=1)

    # delete the table
    delete_table(table_name)

    # print the end time
    print_time()


if __name__ == "__main__":
    # Number of threads to use for concurrent inserts
    num_threads = 100

    # Duration for which to run the inserts (in seconds)
    insert_duration = 60

    # Number of columns in the table
    num_columns = 10

    # Number of rows to insert
    num_rows = 100

    # Size of each column (in characters)
    column_size = 200

    # Table name
    table_name = "table1"

    # Call the insert_large_data function
    insert_large_data(
        num_threads, insert_duration, num_columns, num_rows, column_size, table_name
    )
