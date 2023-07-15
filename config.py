import sys
import os

DB_FILE = 'data/content.db'
CREATE_SQL = 'sql/tables.sql'

base_path = os.getcwd()
db_path = os.path.join(base_path,DB_FILE)
create_sql_file_path = os.path.join(base_path,CREATE_SQL)

# print("="*30)
# print(f'Base Path: {base_path}\nDB Path: {db_path}\nSQL File Path: {create_sql_file_path}')
# print("="*30)