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
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                         (username, password_hash))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_user_by_username(self, username):
        conn = self._connect()
        user = conn.execute(
            '''SELECT id, username, password_hash, created_at
               FROM users
               WHERE username = ?''',
            (username,)).fetchone()
        conn.close()
        return user

    def add_device(self, name, description, created_by):
        conn = self._connect()
        try:
            conn.execute(
                'INSERT INTO devices (name, description, created_by) VALUES (?, ?, ?)',
                (name, description, created_by)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print('Error adding device:', e)
            return False
        finally:
            conn.close()

    def get_device_by_id(self, device_id):
        conn = self._connect()
        device = conn.execute(
            '''SELECT d.id, d.name, d.description, d.created_by, d.created_at,
               u.username AS creator_username
               FROM devices d
               JOIN users u ON d.created_by = u.id
               WHERE d.id = ?''', (device_id,)).fetchone()
        conn.close()
        return device

    def update_device(self, device_id, name, description):
        conn = self._connect()
        conn.execute('UPDATE devices SET name = ?, description = ? WHERE id = ?',
                     (name, description, device_id)
        )
        conn.commit()
        conn.close()

    def delete_device(self, device_id):
        conn = self._connect()
        conn.execute('DELETE FROM devices WHERE id = ?', (device_id,))
        conn.commit()
        conn.close()

    def search_devices(self, query=None, user_id=None, owned=False, page=1, limit=20):
        conn = self._connect()
        search = f'%{query}%' if query else '%'
        params = [search, search]

        clauses = ['(d.name LIKE ? OR d.description LIKE ?)']

        if owned and user_id:
            clauses.append(
                '''EXISTS (
                   SELECT 1 FROM reservations r_check
                   WHERE r_check.device_id = d.id
                   AND r_check.user_id = ?
                   AND r_check.reserved_until > strftime('%s', 'now')
                   AND r_check.ended_at IS NULL
                   )''')
            params.append(user_id)

        where_sql = ' AND '.join(clauses)

        # COUNT query
        count_sql = f'SELECT COUNT(*) FROM devices d WHERE {where_sql};'

        # main query
        sql = f'''
        WITH RankedReservations AS (
            SELECT
                r.id, r.device_id, r.user_id, r.reserved_until,
                u.username AS reserver_username,
                ROW_NUMBER() OVER (PARTITION BY r.device_id ORDER BY r.reserved_until ASC) as rn
            FROM reservations r
            JOIN users u ON r.user_id = u.id
            WHERE r.reserved_until > strftime('%s', 'now') AND r.ended_at IS NULL
        )
        SELECT
            d.id, d.name, d.description, d.created_at,
            u_creator.username AS creator_username,
            COALESCE(rr_current_user.is_current_user_reservation, 0) AS current_user_has_reservation,
            rr_any_user.id AS reservation_id,
            rr_any_user.user_id AS reservation_user_id,
            rr_any_user.reserved_until AS reservation_reserved_until,
            rr_any_user.reserver_username AS reservation_username
        FROM devices d
        JOIN users u_creator ON d.created_by = u_creator.id
        LEFT JOIN (
            SELECT device_id, 1 AS is_current_user_reservation
            FROM RankedReservations
            WHERE user_id = ? AND rn = 1
        ) AS rr_current_user ON d.id = rr_current_user.device_id
        LEFT JOIN (
            SELECT * FROM RankedReservations WHERE rn = 1
        ) AS rr_any_user ON d.id = rr_any_user.device_id
        WHERE {where_sql}
        ORDER BY d.id ASC
        LIMIT ? OFFSET ?;
        '''

        try:
            count_cursor = conn.execute(count_sql, params)
            total = count_cursor.fetchone()[0]

            query_params = params + [user_id if user_id else 0, limit, (page - 1) * limit]
            cursor = conn.execute(sql, query_params)
            items = [dict(row) for row in cursor.fetchall()]

            return {
                'total': total,
                'items': items
            }

        except sqlite3.Error as e:
            print('search_devices failed:', e)
            return {
                'total': 0,
                'items': []
            }
        finally:
            conn.close()

    def get_all_devices(self, user_id=None, owned=False, page=1, limit=20):
        return self.search_devices(query=None, user_id=user_id, owned=owned, page=page, limit=limit)

    def create_reservation(self, user_id, device_id, reserved_until):
        conn = self._connect()
        try:
            reserved_until = int(datetime.fromisoformat(reserved_until).timestamp())
            conn.execute(
                'INSERT INTO reservations (user_id, device_id, reserved_until) VALUES (?, ?, ?)',
                (user_id, device_id, reserved_until)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print('Error creating reservation:', e)
            return False
        finally:
            conn.close()

    def get_reservations_by_user(self, user_id):
        conn = self._connect()
        reservations = conn.execute(
            '''SELECT r.id, r.user_id, r.device_id, r.reserved_until,
                    r.created_at, r.ended_at, d.name AS device_name
               FROM reservations r
               JOIN devices d ON r.device_id = d.id
               JOIN users u ON r.user_id = u.id
               WHERE u.username = ? 
               ORDER BY r.reserved_until DESC''',
            (user_id,)
        ).fetchall()
        conn.close()
        return reservations

    def get_active_reservations_for_device(self, device_id, current_time):
        conn = self._connect()
        reservations = conn.execute(
            '''SELECT id, user_id, device_id, reserved_until, created_at, ended_at
               FROM reservations
               WHERE device_id = ? AND reserved_until > ? AND ended_at IS NULL''',
            (device_id, current_time)
        ).fetchall()
        conn.close()
        return reservations

    def cancel_reservation(self, reservation_id, user_id):
        conn = self._connect()
        conn.execute(
            '''UPDATE reservations 
               SET ended_at = strftime('%s','now')
               WHERE id = ?''',
            (reservation_id,))
        conn.commit()
        conn.close()

    def get_active_reservation_for_device(self, device_id):
        conn = self._connect()
        reservation = conn.execute(
            '''SELECT r.id, r.user_id, r.device_id, r.reserved_until,
                        r.created_at, r.ended_at, u.username
               FROM reservations r
               JOIN users u ON r.user_id = u.id
               WHERE r.device_id = ?
               AND r.reserved_until > strftime('%s','now')
               AND r.ended_at IS NULL
               ORDER BY r.reserved_until
               LIMIT 1''',
            (device_id,)
        ).fetchone()
        conn.close()
        return reservation

    def get_active_reservations_by_user(self, username):
        conn = self._connect()
        cursor = conn.execute(
            '''SELECT r.id, d.name, r.reserved_until
               FROM reservations r
               JOIN devices d ON r.device_id = d.id
               JOIN users u ON r.user_id = u.id
               WHERE u.username = ? AND r.reserved_until > strftime('%s', 'now')
               AND ended_at IS NULL''',
            (username,))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_devices_created_by_user(self, username):
        conn = self._connect()
        cursor = conn.execute(
            '''SELECT d.id, d.name, d.description
               FROM devices d
               JOIN users u ON d.created_by = u.id
               WHERE u.username = ?''',
            (username,))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_last_reservations_by_user(self, username, limit=10):
        conn = self._connect()
        cursor = conn.execute(
            '''SELECT r.id, d.name, 
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
               LIMIT ?''',
            (username, limit))
        results = cursor.fetchall()
        conn.close()
        return results

    def add_comment(self, device_id, user_id, content):
        conn = self._connect()
        try:
            conn.execute(
                'INSERT INTO comments (device_id, user_id, content) VALUES (?, ?, ?)',
                (device_id, user_id, content)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f'Error adding comment: {e}')
            return False
        finally:
            conn.close()

    def get_comments_for_device(self, device_id):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT c.id, c.content, c.created_at, u.username AS author_username, c.user_id
                   FROM comments c
                   JOIN users u ON c.user_id = u.id
                   WHERE c.device_id = ?
                   ORDER BY c.created_at DESC''',
                (device_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_comment_by_id(self, comment_id):
        conn = self._connect()
        comment = conn.execute(
            '''SELECT id, device_id, user_id, content, created_at
               FROM comments
               WHERE id = ?''', (comment_id,)).fetchone()
        conn.close()
        return comment

    def delete_comment(self, comment_id, user_id_who_is_deleting):
        conn = self._connect()
        try:
            # check if user deleting is the author
            comment = self.get_comment_by_id(comment_id)
            if not comment:
                print('Comment not found for deletion.')
                return False
            if comment['user_id'] != user_id_who_is_deleting:
                print('User not authorized to delete this comment.')
                return False

            conn.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f'Error deleting comment: {e}')
            return False
        finally:
            conn.close()

    def get_user_device_reservation_durations(self, user_id):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT
                        d.id as device_id,
                        d.name as device_name,
                   SUM(
                        CASE
                            WHEN r.ended_at IS NOT NULL AND r.ended_at > r.created_at
                                THEN r.ended_at - r.created_at
                            WHEN r.ended_at IS NULL AND r.reserved_until > r.created_at
                                THEN r.reserved_until - r.created_at
                            ELSE 0
                        END
                   ) as total_duration_seconds
                   FROM
                        devices d
                   JOIN
                        reservations r ON d.id = r.device_id
                   WHERE
                        r.user_id = ?
                   GROUP BY
                        d.id, d.name
                   HAVING
                        SUM(CASE
                            WHEN r.ended_at IS NOT NULL AND r.ended_at > r.created_at
                            THEN r.ended_at - r.created_at
                            WHEN r.ended_at IS NULL AND r.reserved_until > r.created_at
                            THEN r.reserved_until - r.created_at ELSE 0 END) > 0
                   ORDER BY
                        total_duration_seconds DESC''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f'Error in get_user_device_reservation_durations: {e}')
            return []
        finally:
            conn.close()

    def get_user_device_reservation_counts(self, user_id):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT
                    d.id as device_id,
                    d.name as device_name,
                   COUNT(r.id) as reservation_count
                   FROM
                        devices d
                   JOIN
                        reservations r ON d.id = r.device_id
                   WHERE
                        r.user_id = ?
                   GROUP BY
                        d.id, d.name
                   HAVING
                        COUNT(r.id) > 0 -- #drop devices with no reservations
                ORDER BY
                    reservation_count DESC''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f'Error in get_user_device_reservation_counts: {e}')
            return []
        finally:
            conn.close()
