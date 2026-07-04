import mysql.connector
from config import Config

def alter():
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN photo_path VARCHAR(255);")
        conn.commit()
        print("Column photo_path added.")
    except Exception as e:
        print("Error or already exists:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    alter()
