#!/usr/bin/env python2.7

import sys
import os

DB_FILE = 'data/content.db'
CREATE_SQL = 'sql/tables.sql'

base_path = os.path.dirname(sys.argv[0])
db_path = os.path.join(base_path,DB_FILE)
create_sql_file_path = os.path.join(base_path,CREATE_SQL)

