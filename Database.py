import sqlite3

class Database:
    def __init__(self, db_path):
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_user(self, username, password_hash):
        conn = self._connect()
        try:
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_user_by_username(self, username):
        conn = self._connect()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        return user

    def add_device(self, name, description, created_by):
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO devices (name, description, created_by) VALUES (?, ?, ?)",
                (name, description, created_by)
            )
            conn.commit()
            return True
        except Exception as e:
            print("Error adding device:", e)
            return False
        finally:
            conn.close()

    def get_all_devices(self):
        conn = self._connect()
        try:
            devices = conn.execute("SELECT * FROM devices").fetchall()
            return devices
        finally:
            conn.close()
