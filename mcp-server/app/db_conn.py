#import mysql.connector
import sqlite3

def get_db_connection():
    conn = sqlite3.connect("<path for sqlite db file")
    conn.row_factory = sqlite3.Row  # enables dict-like access
    return conn

"""MySQL connetion
def get_db_connection():
    return mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="password123",
    database="flicket")
"""