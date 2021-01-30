import MySQLdb

from mysql_config import Config as config

def connect_db():
    db=MySQLdb.connect(host=config.MYSQL_HOST,
                       user=config.MYSQL_USER,
                       passwd=config.MYSQL_PASSWD,
                       db=config.MYSQL_DB)
    return db

def db_init():
    db=connect_db()
    cursor = db.cursor()
    #cursor.execute("DROP TABLE IF EXISTS sensors;")
    #cursor.execute("DROP TABLE IF EXISTS log;")
    #cursor.execute("DROP TABLE IF EXISTS measurements;")

    cursor.execute("CREATE TABLE measurements (time DATETIME DEFAULT NOW(), id INT, val REAL);")
    cursor.execute("CREATE TABLE sensors (id INT NOT NULL AUTO_INCREMENT, sn CHAR(16), name VARCHAR(256), stype VARCHAR(256), PRIMARY KEY (id));")
    cursor.execute("CREATE TABLE log (time DATETIME DEFAULT NOW(), msg VARCHAR(256));")

    db.commit()

if __name__ == "__main__":
    db_init()
