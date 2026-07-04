import mysql.connector
import os
from config import Config

def init_db():
    try:
        # Connect without specific DB first
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        cursor = connection.cursor()
        
        with open('database.sql', 'r') as f:
            sql_script = f.read()
            
        # Execute each statement
        for statement in sql_script.split(';'):
            if statement.strip():
                try:
                    cursor.execute(statement)
                except Exception as e:
                    print(f"Statement executed with warning or error (usually safe to ignore if already exists): {e}")
        
        connection.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing DB: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    init_db()
