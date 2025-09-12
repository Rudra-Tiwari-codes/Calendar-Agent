import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SQL_PATH = "programs/integration/calendar/"
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL not set")

def get_connection():
    return psycopg2.connect(DATABASE_URL)


def run_sql_file(file_path):
    with open(file_path, 'r') as file:
        sql = file.read()
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
    except Exception as e:
        print(f"Error: {e}\n")


def run_ddl():
    ddl_path = Path(SQL_PATH + "DDL")
    for sql_file in sorted(ddl_path.glob("*.sql")):
        run_sql_file(sql_file)


def run_dml():
    dml_path = Path(SQL_PATH + "DML")
    for sql_file in sorted(dml_path.glob("*.sql")):
        run_sql_file(sql_file)


def view_table(table_name):
    print(f"Table Content: {table_name}")
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 100;")
                rows = cursor.fetchall()
                for row in rows:
                    print(row)
                if not rows:
                    print("No rows found.")
    except Exception as e:
        print(f"Error: {e}")
    print("")


if __name__ == "__main__":
    run_ddl()
    run_dml()
    # view_table("project_two.matthew")
