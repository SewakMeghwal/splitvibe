"""
Database & Seed Generator for SquadVault (Phase 2 Updated)
Includes User Settings, Itineraries, and extended user profiles.
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
        handle TEXT NOT NULL,
        avatar TEXT NOT NULL,
        bio TEXT,
        venmo_handle TEXT,
        zelle_handle TEXT
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

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_demo_data(conn)

    conn.close()

def seed_demo_data(conn):
    cursor = conn.cursor()

    users = [
        ("u1", "Alex Rivera", "@alex_r", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80", "Design lead & cabin planner 🏕️", "@alex-rivera-venmo", "alex@rivera.com"),
        ("u2", "Maya Lin", "@maya_tech", "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80", "Software dev & coffee enthusiast ☕", "@maya-lin-venmo", "maya@lin.com"),
        ("u3", "Sam Chen", "@sam_c", "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150&auto=format&fit=crop&q=80", "Photographer & master chef 🍳", "@sam-chen-venmo", "sam@chen.com"),
        ("u4", "Jordan Taylor", "@jordan_t", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80", "Traveler & playlist curator 🎧", "@jordan-taylor-venmo", "jordan@taylor.com")
    ]
    cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", users)

    # User Settings
    settings = [
        ("u1", "deep-space", 1, 1, 1, 1),
        ("u2", "cyberpunk", 1, 1, 1, 1),
        ("u3", "emerald", 1, 1, 1, 1),
        ("u4", "light", 1, 1, 1, 1)
    ]
    cursor.executemany("INSERT INTO user_settings VALUES (?, ?, ?, ?, ?, ?)", settings)

    squads = [
        ("sq1", "Tahoe Ski Roadtrip 🏔️", "Weekend trip to South Lake Tahoe cabin with the crew!", "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=300&auto=format&fit=crop&q=80", "Travel"),
        ("sq2", "Apartment 302 Roomies 🏠", "Monthly bills, grocery runs, and household supplies.", "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=300&auto=format&fit=crop&q=80", "Housing"),
        ("sq3", "Friday Night Foodies 🍕", "Weekly fine dining and food truck adventures around town.", "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=300&auto=format&fit=crop&q=80", "Dining")
    ]
    cursor.executemany("INSERT INTO squads (id, name, description, avatar, category) VALUES (?, ?, ?, ?, ?)", squads)

    members = [
        ("sq1", "u1"), ("sq1", "u2"), ("sq1", "u3"), ("sq1", "u4"),
        ("sq2", "u1"), ("sq2", "u2"), ("sq2", "u3"),
        ("sq3", "u1"), ("sq3", "u2"), ("sq3", "u3"), ("sq3", "u4")
    ]
    cursor.executemany("INSERT INTO squad_members VALUES (?, ?)", members)

    expenses = [
        (
            "exp1", "sq1", "u1", "Tahoe Lake Cabin Rental (3 Nights)", 600.0, "Travel", "2026-09-02",
            json.dumps({"u1": 150.0, "u2": 150.0, "u3": 150.0, "u4": 150.0}),
            "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=600&auto=format&fit=crop&q=80",
            "Booked cozy 4-bedroom cabin right near the ski lift."
        ),
        (
            "exp2", "sq1", "u3", "Gourmet BBQ Grocery Run 🥩", 180.0, "Groceries", "2026-09-03",
            json.dumps({"u1": 45.0, "u2": 45.0, "u3": 45.0, "u4": 45.0}),
            "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&auto=format&fit=crop&q=80",
            "Steaks, veggies, snacks, and morning coffee beans."
        ),
        (
            "exp3", "sq1", "u2", "Ski Passes & Gear Rental", 240.0, "Entertainment", "2026-09-04",
            json.dumps({"u1": 60.0, "u2": 60.0, "u3": 60.0, "u4": 60.0}),
            "https://images.unsplash.com/photo-1565992441121-4367c2967103?w=600&auto=format&fit=crop&q=80",
            "Discounted group lift tickets!"
        ),
        (
            "exp4", "sq2", "u2", "Gigabit Internet & Utilities", 120.0, "Bills", "2026-09-01",
            json.dumps({"u1": 40.0, "u2": 40.0, "u3": 40.0}),
            "https://images.unsplash.com/photo-1544717305-2782549b5136?w=600&auto=format&fit=crop&q=80",
            "September high speed fiber internet connection."
        ),
        (
            "exp5", "sq3", "u4", "Artisan Wood-fired Pizza Night 🍕", 140.0, "Dining", "2026-09-06",
            json.dumps({"u1": 35.0, "u2": 35.0, "u3": 35.0, "u4": 35.0}),
            "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80",
            "Truffle mushroom and spicy pepperoni pies."
        )
    ]
    cursor.executemany("INSERT INTO expenses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", expenses)

    posts = [
        (
            "p1", "u1", "sq1", "Tahoe sunrise views from the deck! Cabin trip is officially underway ☕❄️",
            "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=800&auto=format&fit=crop&q=80",
            "photo", 14, "exp1"
        ),
        (
            "r1", "u3", "sq1", "Chef Sam in action! Grilling for 4 hungry skiers after a full day on the slopes 🔥🥩",
            "https://assets.mixkit.co/videos/preview/mixkit-barbecue-on-a-sunny-afternoon-42930-large.mp4",
            "reel", 28, "exp2"
        ),
        (
            "p2", "u4", "sq3", "Best wood-fired crust in town hands down! Thanks @sam_c and @maya_tech for coming out 🎉",
            "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800&auto=format&fit=crop&q=80",
            "photo", 19, "exp5"
        ),
        (
            "r2", "u2", "sq1", "Carving down the fresh powder run in Lake Tahoe! ⛷️ Mountain vibes!",
            "https://assets.mixkit.co/videos/preview/mixkit-snowboarder-carving-down-a-snowy-mountain-41584-large.mp4",
            "reel", 42, "exp3"
        )
    ]
    cursor.executemany("INSERT INTO posts (id, user_id, squad_id, caption, media_url, type, likes, expense_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", posts)

    comments = [
        ("c1", "p1", "u2", "That view is unmatched! Can't wait for morning runs tomorrow! 🙌"),
        ("c2", "p1", "u3", "I brought the hot chocolate mixes 🍫☕"),
        ("c3", "r1", "u1", "Legendary dinner! Worth every single penny of that BBQ split 🔥")
    ]
    cursor.executemany("INSERT INTO comments (id, post_id, user_id, text) VALUES (?, ?, ?, ?)", comments)

    messages = [
        ("m1", "group", "u1", "sq1", "Hey squad! Cabin check-in code is 4921# 🔑 Let me know when everyone lands!", None),
        ("m2", "group", "u3", "sq1", "Just picked up the BBQ groceries! I'll add the expense split now 🥩", None),
        ("m3", "group", "u3", "sq1", "Shared an expense request!", json.dumps({"title": "Gourmet BBQ Grocery Run 🥩", "amount": 45.0, "expense_id": "exp2"})),
        ("m4", "direct", "u2", "u1", "Hey Alex! Thanks for covering the cabin deposit upfront!", None),
        ("m5", "direct", "u1", "u2", "No problem at all Maya! The debt solver will balance it out nicely 🚀", None)
    ]
    cursor.executemany("INSERT INTO messages (id, chat_type, sender_id, target_id, text, expense_request) VALUES (?, ?, ?, ?, ?, ?)", messages)

    # Sample Itineraries
    itineraries = [
        ("it1", "sq1", "Ski Lift & Mountain Pass Run", "2026-09-09", "09:00 AM", "Heavenly Ski Resort", 60.0, 4, "u1"),
        ("it2", "sq1", "Sunset Lake Tahoe Dinner", "2026-09-09", "06:30 PM", "The Boathouse Grill", 45.0, 3, "u3"),
        ("it3", "sq3", "Downtown Food Truck Rally", "2026-09-12", "07:00 PM", "Civic Center Plaza", 25.0, 4, "u4")
    ]
    cursor.executemany("INSERT INTO itineraries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", itineraries)

    conn.commit()
