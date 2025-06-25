#!/usr/bin/env python3
'''stress test for slotkeeper'''
import sqlite3
import hashlib
import time

DB_PATH = 'database.db'
N_USERS = 100000
N_DEVICES = 100000
COMMENTS_PER_DEVICE = 100

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def insert_users(conn, n):
    print('Inserting users...')
    users = [(f'user{i}', hash_password(f'pass{i}')) for i in range(n)]
    conn.executemany('INSERT INTO users (username, password_hash) VALUES (?, ?)', users)
    conn.commit()

def insert_devices(conn, n):
    print('Inserting devices...')
    devices = [(f'device{i}', f'description of device {i}', i % N_USERS + 1) for i in range(n)]
    conn.executemany('INSERT INTO devices (name, description, created_by) VALUES (?, ?, ?)',
                     devices)
    conn.commit()

def insert_comments(conn, n_devices, comments_per_device):
    print('Inserting comments...')
    start_time = time.time()
    batch = []
    batch_size = 10_000

    for d in range(n_devices):
        device_id = d + 1
        for c in range(comments_per_device):
            user_id = (d + c) % N_USERS + 1
            content = f'Comment {c} for device {device_id}'
            batch.append((device_id, user_id, content))

            if len(batch) >= batch_size:
                conn.executemany(
                    'INSERT INTO comments (device_id, user_id, content) VALUES (?, ?, ?)',
                    batch
                )
                conn.commit()
                print(f'Inserted {len(batch)} comments (total so far: {d * comments_per_device + c + 1})')
                batch = []

    if batch:
        conn.executemany(
            'INSERT INTO comments (device_id, user_id, content) VALUES (?, ?, ?)',
            batch
        )
        conn.commit()
        print(f'Inserted final batch of {len(batch)} comments')

    elapsed = time.time() - start_time
    print(f'Inserted all comments in {elapsed:.2f} seconds')

def main():
    conn = sqlite3.connect(DB_PATH)
    insert_users(conn, N_USERS)
    insert_devices(conn, N_DEVICES)
    insert_comments(conn, N_DEVICES, COMMENTS_PER_DEVICE)
    conn.close()

if __name__ == '__main__':
    main()
