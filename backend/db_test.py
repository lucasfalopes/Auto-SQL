import pg8000
import os
from dotenv import load_dotenv

load_dotenv()

con = pg8000.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

tables = []

for row in con.run("select TABLE_NAME from information_schema.tables WHERE table_schema='public' order by table_name"):
    tables.append(row[0])

print(f"All tables listed: {tables}")

for table in tables:
    print(f"Current table: {table}")
    for row in con.run(f"select column_name, data_type from information_schema.columns where table_name = '{table}'"):
        print(row)

con.close()