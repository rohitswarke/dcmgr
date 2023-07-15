import config
import controller

if __name__ == "__main__":
    print("Creating database...")
    con = controller.Controller(config.db_path)
    con.create_db(config.create_sql_file_path)
    con.close()
    print("Database creation successful")
