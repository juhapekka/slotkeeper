-- Create user table in SQLite
-- maximum user name lenght 32
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL CHECK(length(username) <= 32),
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create reservable device table
-- maximum device name lenght 32
-- maximum description size 4k
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK(length(name) <= 32),
    description TEXT CHECK(length(description) <= 4096),
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Create reservations table
CREATE TABLE reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    device_id INTEGER NOT NULL,
    reserved_until INTEGER NOT NULL,
    created_at INTEGER DEFAULT (strftime('%s','now')),
    ended_at INTEGER DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (device_id) REFERENCES devices(id)
);