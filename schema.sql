-- Create user table in SQLite
-- maximum user name lenght 32
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL CHECK(length(username) <= 32),
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- index for users if UNIQUE somehow failed us
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

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

-- Indexes for devices
CREATE INDEX IF NOT EXISTS idx_devices_created_by ON devices(created_by);
CREATE INDEX IF NOT EXISTS idx_devices_name ON devices(name);

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

-- Indexes for reservations
CREATE INDEX IF NOT EXISTS idx_reservations_user_id ON reservations(user_id);
CREATE INDEX IF NOT EXISTS idx_reservations_device_id ON reservations(device_id);
CREATE INDEX IF NOT EXISTS idx_reservations_device_active ON reservations(device_id, reserved_until, ended_at);
CREATE INDEX IF NOT EXISTS idx_reservations_user_active ON reservations(user_id, reserved_until, ended_at);
CREATE INDEX IF NOT EXISTS idx_reservations_created_at ON reservations(created_at);

-- Create comments table
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL CHECK(length(content) <= 1024),
    created_at INTEGER DEFAULT (strftime('%s','now')),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for comments
CREATE INDEX IF NOT EXISTS idx_comments_device_id ON comments(device_id);
CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_device_created_at ON comments(device_id, created_at);