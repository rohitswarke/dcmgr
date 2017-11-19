#!/usr/bin/env python2.7
import config
import controller

if __name__ == "__main__":
    con = controller.Controller(config.db_path)
    con.create_db(config.create_sql_file_path)
    con.close()
