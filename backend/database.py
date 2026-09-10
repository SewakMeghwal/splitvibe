"""
Database Engine for SplitVibe
Provides SQLite persistence with clean table initialization.
"""

import sqlite3
import json
import os
from typing import Dict, List, Any

DB_FILE = os.path.join(os.path.dirname(__file__), "splitvibe.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        handle TEXT NOT NULL UNIQUE,
        avatar TEXT NOT NULL,
        bio TEXT,
        venmo_handle TEXT,
        zelle_handle TEXT,
        password_hash TEXT NOT NULL
    )
    """)

    # User Settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id TEXT PRIMARY KEY,
        theme TEXT DEFAULT 'deep-space',
        notify_expenses INTEGER DEFAULT 1,
        notify_settlements INTEGER DEFAULT 1,
        notify_chat INTEGER DEFAULT 1,
        notify_likes INTEGER DEFAULT 1
    )
    """)

    # Squads
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS squads (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        avatar TEXT NOT NULL,
        category TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Squad Members
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS squad_members (
        squad_id TEXT,
        user_id TEXT,
        PRIMARY KEY (squad_id, user_id)
    )
    """)

    # Expenses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id TEXT PRIMARY KEY,
        squad_id TEXT NOT NULL,
        paid_by TEXT NOT NULL,
        title TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        date TEXT NOT NULL,
        splits_json TEXT NOT NULL,
        memory_photo TEXT,
        notes TEXT
    )
    """)

    # Posts & Reels
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        squad_id TEXT,
        caption TEXT NOT NULL,
        media_url TEXT NOT NULL,
        type TEXT NOT NULL,
        likes INTEGER DEFAULT 0,
        expense_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Comments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id TEXT PRIMARY KEY,
        post_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Messages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        chat_type TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        text TEXT NOT NULL,
        expense_request TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Itineraries
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS itineraries (
        id TEXT PRIMARY KEY,
        squad_id TEXT NOT NULL,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        location TEXT,
        cost REAL DEFAULT 0.0,
        votes INTEGER DEFAULT 1,
        created_by TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()
