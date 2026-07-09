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


def update_score(user_id, new_score):
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET score = %s WHERE id = %s AND (score IS NULL OR score < %s)",
            (new_score, user_id, new_score)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"Gagal update score: {e}")
        return False
    finally:
        cursor.close()
        conn.close()