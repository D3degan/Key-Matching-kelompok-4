import mysql.connector
from mysql.connector import Error


def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",       
            database="db_game_alpro2"  
        )
        return conn
    except Error as e:
        print(f"Gagal konek ke DB: {e}")
        return None