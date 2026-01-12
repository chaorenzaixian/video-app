import sqlite3
import pymysql
import os

MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'video_app',
    'password': 'RmYtmssLzZMXjbbM',
    'database': 'video_app',
    'charset': 'utf8mb4'
}

SQLITE_DB_PATH = 'app.db'

def migrate():
    print("Starting migration...")
    if not os.path.exists(SQLITE_DB_PATH):
        print("Error: app.db not found")
        return
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cur = sqlite_conn.cursor()
    try:
        mysql_conn = pymysql.connect(**MYSQL_CONFIG)
        mysql_cur = mysql_conn.cursor()
        print("MySQL connected!")
    except Exception as e:
        print(f"MySQL error: {e}")
        return
    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [r[0] for r in sqlite_cur.fetchall()]
    print(f"Found {len(tables)} tables")
    mysql_cur.execute("SET FOREIGN_KEY_CHECKS=0")
    total = 0
    for tbl in tables:
        try:
            sqlite_cur.execute(f"PRAGMA table_info({tbl})")
            cols = [r[1] for r in sqlite_cur.fetchall()]
            col_defs = ", ".join([f"`{c}` TEXT" for c in cols])
            mysql_cur.execute(f"DROP TABLE IF EXISTS `{tbl}`")
            mysql_cur.execute(f"CREATE TABLE `{tbl}` ({col_defs})")
            sqlite_cur.execute(f"SELECT * FROM `{tbl}`")
            rows = sqlite_cur.fetchall()
            if rows:
                ph = ", ".join(["%s"] * len(cols))
                cs = ", ".join([f"`{c}`" for c in cols])
                sql = f"INSERT INTO `{tbl}` ({cs}) VALUES ({ph})"
                cnt = 0
                for row in rows:
                    vals = [v.decode('utf-8') if isinstance(v, bytes) else v for v in row]
                    try:
                        mysql_cur.execute(sql, vals)
                        cnt += 1
                    except:
                        pass
                mysql_conn.commit()
                total += cnt
                print(f"  {tbl}: {cnt} rows")
            else:
                print(f"  {tbl}: empty")
        except Exception as e:
            print(f"  {tbl}: failed - {e}")
    mysql_cur.execute("SET FOREIGN_KEY_CHECKS=1")
    mysql_conn.commit()
    sqlite_conn.close()
    mysql_conn.close()
    print(f"Done! Total {total} rows migrated.")

if __name__ == "__main__":
    migrate()
