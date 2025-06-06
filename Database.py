import sqlite3
from datetime import datetime

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
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                         (username, password_hash))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_user_by_username(self, username):
        conn = self._connect()
        user = conn.execute("""SELECT *
                               FROM users
                               WHERE username = ?""",
                            (username,)).fetchone()
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
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Devices.id, Devices.name, Devices.description,
                Users.username AS creator_username
                FROM Devices
                JOIN Users ON Devices.created_by = Users.id
                """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_device_by_id(self, device_id):
        conn = self._connect()
        device = conn.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
        conn.close()
        return device

    def update_device(self, device_id, name, description):
        conn = self._connect()
        conn.execute("UPDATE devices SET name = ?, description = ? WHERE id = ?",
                     (name, description, device_id)
        )
        conn.commit()
        conn.close()

    def delete_device(self, device_id):
        conn = self._connect()
        conn.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        conn.commit()
        conn.close()

    def search_devices(self, query):
        conn = self._connect()
        search = f'%{query}%'
        devices = conn.execute(
            """SELECT * 
               FROM devices 
               WHERE name LIKE ? OR description LIKE ?""",
            (search, search)
        ).fetchall()
        conn.close()
        return devices

    def create_reservation(self, user_id, device_id, reserved_until):
        conn = self._connect()
        try:
            reserved_until = int(datetime.fromisoformat(reserved_until).timestamp())
            conn.execute(
                "INSERT INTO reservations (user_id, device_id, reserved_until) VALUES (?, ?, ?)",
                (user_id, device_id, reserved_until)
            )
            conn.commit()
            return True
        except Exception as e:
            print("Error creating reservation:", e)
            return False
        finally:
            conn.close()

    def get_reservations_by_user(self, user_id):
        conn = self._connect()
        reservations = conn.execute(
            """SELECT r.*, d.name AS device_name 
               FROM reservations r 
               JOIN devices d ON r.device_id = d.id 
               WHERE r.user_id = ? 
               ORDER BY r.reserved_until DESC""",
            (user_id,)
        ).fetchall()
        conn.close()
        return reservations

    def get_active_reservations_for_device(self, device_id, current_time):
        conn = self._connect()
        reservations = conn.execute(
            "SELECT * FROM reservations WHERE device_id = ? AND reserved_until > ?  AND ended_at IS NULL",
            (device_id, current_time)
        ).fetchall()
        conn.close()
        return reservations

    def cancel_reservation(self, reservation_id, user_id):
        conn = self._connect()
        conn.execute(
            """UPDATE reservations 
               SET ended_at = strftime('%s','now')
               WHERE id = ?""",
            (reservation_id,))
        conn.commit()
        conn.close()

    def get_active_reservation_for_device(self, device_id):
        conn = self._connect()
        reservation = conn.execute(
            """SELECT r.*, u.username 
               FROM reservations r 
               JOIN users u ON r.user_id = u.id 
               WHERE r.device_id = ? 
               AND r.reserved_until > strftime('%s','now') AND ended_at IS NULL
               ORDER BY r.reserved_until
               LIMIT 1""",
            (device_id,)
        ).fetchone()
        conn.close()
        return reservation

    def get_active_reservations_by_user(self, username):
        conn = self._connect()
        cursor = conn.execute(
            """SELECT r.id, d.name, r.reserved_until
               FROM reservations r
               JOIN devices d ON r.device_id = d.id
               JOIN users u ON r.user_id = u.id
               WHERE u.username = ? AND r.reserved_until > strftime('%s', 'now')
               AND ended_at IS NULL""",
            (username,))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_devices_created_by_user(self, username):
        conn = self._connect()
        cursor = conn.execute(
            """SELECT d.id, d.name, d.description
               FROM devices d
               JOIN users u ON d.created_by = u.id
               WHERE u.username = ?""",
            (username,))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_last_reservations_by_user(self, username, limit=10):
        conn = self._connect()
        cursor = conn.execute(
            """SELECT r.id, d.name, 
                   CASE 
                       WHEN r.ended_at IS NOT NULL THEN r.ended_at 
                       ELSE r.reserved_until 
                   END AS effective_end,
                   r.created_at
               FROM reservations r
               LEFT JOIN devices d ON r.device_id = d.id
               JOIN users u ON r.user_id = u.id
               WHERE u.username = ?
               ORDER BY r.created_at DESC
               LIMIT ?""",
            (username, limit))
        results = cursor.fetchall()
        conn.close()
        return results
