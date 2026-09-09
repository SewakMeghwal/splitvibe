"""
SplitVibe FastAPI Server
Includes Settings APIs, Profile Updates, OCR Receipt Parser, Currency FX, and Itineraries.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import uuid
import os
from datetime import datetime

from backend.database import get_db_connection, init_db
from backend.debt_solver import simplify_debts
from backend.chat_ws import manager
from backend.ocr_parser import parse_receipt_text
from backend.currency import convert_currency, EXCHANGE_RATES

app = FastAPI(title="SplitVibe Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

# Models
class UserUpdate(BaseModel):
    name: str
    handle: str
    avatar: str
    bio: Optional[str] = ""
    venmo_handle: Optional[str] = ""
    zelle_handle: Optional[str] = ""

class SettingsUpdate(BaseModel):
    theme: str
    notify_expenses: bool
    notify_settlements: bool
    notify_chat: bool
    notify_likes: bool

class ExpenseCreate(BaseModel):
    squad_id: str
    paid_by: str
    title: str
    amount: float
    category: str
    splits: Dict[str, float]
    currency: Optional[str] = "USD"
    memory_photo: Optional[str] = None
    notes: Optional[str] = None

class PostCreate(BaseModel):
    user_id: str
    squad_id: Optional[str] = None
    caption: str
    media_url: str
    type: str
    expense_id: Optional[str] = None

class CommentCreate(BaseModel):
    user_id: str
    text: str

class MessageCreate(BaseModel):
    chat_type: str
    sender_id: str
    target_id: str
    text: str
    expense_request: Optional[Dict[str, Any]] = None

class SettleCreate(BaseModel):
    squad_id: str
    from_user: str
    to_user: str
    amount: float

class ItineraryCreate(BaseModel):
    squad_id: str
    title: str
    date: str
    time: str
    location: Optional[str] = ""
    cost: float = 0.0
    created_by: str

class VoiceParseRequest(BaseModel):
    voice_text: str

# --- USERS & PROFILE ---

@app.get("/api/users")
def get_users():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return [dict(u) for u in users]

@app.put("/api/users/{user_id}")
def update_user_profile(user_id: str, profile: UserUpdate):
    conn = get_db_connection()
    conn.execute("""
        UPDATE users 
        SET name = ?, handle = ?, avatar = ?, bio = ?, venmo_handle = ?, zelle_handle = ?
        WHERE id = ?
    """, (profile.name, profile.handle, profile.avatar, profile.bio, profile.venmo_handle, profile.zelle_handle, user_id))
    conn.commit()
    conn.close()
    return {"status": "updated", "user_id": user_id}

@app.get("/api/users/{user_id}/settings")
def get_user_settings(user_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return {
            "user_id": user_id,
            "theme": "deep-space",
            "notify_expenses": True,
            "notify_settlements": True,
            "notify_chat": True,
            "notify_likes": True
        }
    return dict(row)

@app.put("/api/users/{user_id}/settings")
def update_user_settings(user_id: str, settings: SettingsUpdate):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO user_settings (user_id, theme, notify_expenses, notify_settlements, notify_chat, notify_likes)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            theme = excluded.theme,
            notify_expenses = excluded.notify_expenses,
            notify_settlements = excluded.notify_settlements,
            notify_chat = excluded.notify_chat,
            notify_likes = excluded.notify_likes
    """, (user_id, settings.theme, int(settings.notify_expenses), int(settings.notify_settlements), int(settings.notify_chat), int(settings.notify_likes)))
    conn.commit()
    conn.close()
    return {"status": "settings_saved"}

# --- SQUADS & EXPENSES ---

@app.get("/api/squads")
def get_squads():
    conn = get_db_connection()
    squads = conn.execute("SELECT * FROM squads").fetchall()
    result = []
    for s in squads:
        sq = dict(s)
        m_rows = conn.execute("""
            SELECT u.* FROM users u 
            JOIN squad_members sm ON u.id = sm.user_id 
            WHERE sm.squad_id = ?
        """, (sq["id"],)).fetchall()
        sq["members"] = [dict(m) for m in m_rows]
        result.append(sq)
    conn.close()
    return result

@app.get("/api/squads/{squad_id}/summary")
def get_squad_summary(squad_id: str):
    conn = get_db_connection()
    expenses_rows = conn.execute("SELECT * FROM expenses WHERE squad_id = ? ORDER BY date DESC", (squad_id,)).fetchall()
    expenses = []
    for e in expenses_rows:
        ed = dict(e)
        ed["splits"] = json.loads(ed["splits_json"])
        expenses.append(ed)

    members_rows = conn.execute("SELECT user_id FROM squad_members WHERE squad_id = ?", (squad_id,)).fetchall()
    member_ids = [m["user_id"] for m in members_rows]

    net_balances = {uid: 0.0 for uid in member_ids}
    for exp in expenses:
        paid_by = exp["paid_by"]
        amount = exp["amount"]
        splits = exp["splits"]

        if paid_by in net_balances:
            net_balances[paid_by] += amount
            
        for uid, split_amt in splits.items():
            if uid in net_balances:
                net_balances[uid] -= split_amt

    simplified = simplify_debts(net_balances)

    conn.close()
    return {
        "squad_id": squad_id,
        "expenses": expenses,
        "net_balances": {uid: round(amt, 2) for uid, amt in net_balances.items()},
        "simplified_debts": simplified
    }

@app.post("/api/expenses")
def create_expense(expense: ExpenseCreate):
    conn = get_db_connection()
    exp_id = f"exp_{uuid.uuid4().hex[:8]}"
    date_str = datetime.now().strftime("%Y-%m-%d")

    # If foreign currency, convert to USD base
    final_amount = expense.amount
    if expense.currency and expense.currency != "USD":
        final_amount = convert_currency(expense.amount, expense.currency, "USD")

    conn.execute("""
        INSERT INTO expenses (id, squad_id, paid_by, title, amount, category, date, splits_json, memory_photo, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        exp_id, expense.squad_id, expense.paid_by, expense.title, final_amount,
        expense.category, date_str, json.dumps(expense.splits), expense.memory_photo, expense.notes
    ))

    if expense.memory_photo:
        post_id = f"p_{uuid.uuid4().hex[:8]}"
        conn.execute("""
            INSERT INTO posts (id, user_id, squad_id, caption, media_url, type, likes, expense_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post_id, expense.paid_by, expense.squad_id,
            f"Added expense: {expense.title} (${final_amount:.2f}) 💳",
            expense.memory_photo, "photo", 0, exp_id
        ))

    conn.commit()
    conn.close()
    return {"status": "success", "expense_id": exp_id, "amount_usd": final_amount}

@app.post("/api/expenses/settle")
def settle_expense(settle: SettleCreate):
    conn = get_db_connection()
    exp_id = f"exp_settle_{uuid.uuid4().hex[:8]}"
    date_str = datetime.now().strftime("%Y-%m-%d")

    splits = {settle.to_user: -settle.amount}

    conn.execute("""
        INSERT INTO expenses (id, squad_id, paid_by, title, amount, category, date, splits_json, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        exp_id, settle.squad_id, settle.from_user, "Payment to user",
        settle.amount, "Settlement", date_str, json.dumps(splits), "Settled debt payment"
    ))

    conn.commit()
    conn.close()
    return {"status": "settled", "expense_id": exp_id}

# --- SOCIAL POSTS & REELS ---

@app.get("/api/posts")
def get_posts(post_type: Optional[str] = Query(None)):
    conn = get_db_connection()
    query = "SELECT * FROM posts"
    params = []
    if post_type:
        query += " WHERE type = ?"
        params.append(post_type)

    query += " ORDER BY created_at DESC"
    posts_rows = conn.execute(query, params).fetchall()

    results = []
    for p in posts_rows:
        pd = dict(p)
        user_row = conn.execute("SELECT name, handle, avatar FROM users WHERE id = ?", (pd["user_id"],)).fetchone()
        pd["user"] = dict(user_row) if user_row else {}

        if pd.get("squad_id"):
            sq_row = conn.execute("SELECT name FROM squads WHERE id = ?", (pd["squad_id"],)).fetchone()
            pd["squad_name"] = sq_row["name"] if sq_row else ""

        cm_rows = conn.execute("""
            SELECT c.*, u.name, u.avatar FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ? ORDER BY c.created_at ASC
        """, (pd["id"],)).fetchall()
        pd["comments"] = [dict(c) for c in cm_rows]

        results.append(pd)

    conn.close()
    return results

@app.post("/api/posts")
def create_post(post: PostCreate):
    conn = get_db_connection()
    post_id = f"p_{uuid.uuid4().hex[:8]}"

    conn.execute("""
        INSERT INTO posts (id, user_id, squad_id, caption, media_url, type, likes, expense_id)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?)
    """, (post_id, post.user_id, post.squad_id, post.caption, post.media_url, post.type, post.expense_id))

    conn.commit()
    conn.close()
    return {"status": "success", "post_id": post_id}

@app.post("/api/posts/{post_id}/like")
def like_post(post_id: str):
    conn = get_db_connection()
    conn.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
    conn.commit()
    row = conn.execute("SELECT likes FROM posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    return {"status": "success", "likes": row["likes"] if row else 0}

@app.post("/api/posts/{post_id}/comments")
def add_comment(post_id: str, comment: CommentCreate):
    conn = get_db_connection()
    cid = f"c_{uuid.uuid4().hex[:8]}"
    conn.execute("""
        INSERT INTO comments (id, post_id, user_id, text) VALUES (?, ?, ?, ?)
    """, (cid, post_id, comment.user_id, comment.text))
    conn.commit()
    conn.close()
    return {"status": "success", "comment_id": cid}

# --- MESSAGES & CHAT ---

@app.get("/api/messages")
def get_messages(chat_type: str, target_id: str, sender_id: Optional[str] = None):
    conn = get_db_connection()
    if chat_type == "group":
        rows = conn.execute("""
            SELECT m.*, u.name as sender_name, u.avatar as sender_avatar 
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.chat_type = 'group' AND m.target_id = ?
            ORDER BY m.timestamp ASC
        """, (target_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT m.*, u.name as sender_name, u.avatar as sender_avatar 
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.chat_type = 'direct' 
            AND ((m.sender_id = ? AND m.target_id = ?) OR (m.sender_id = ? AND m.target_id = ?))
            ORDER BY m.timestamp ASC
        """, (sender_id, target_id, target_id, sender_id)).fetchall()

    results = []
    for r in rows:
        rd = dict(r)
        if rd.get("expense_request"):
            try:
                rd["expense_request"] = json.loads(rd["expense_request"])
            except Exception:
                pass
        results.append(rd)

    conn.close()
    return results

@app.post("/api/messages")
async def send_message(msg: MessageCreate):
    conn = get_db_connection()
    mid = f"m_{uuid.uuid4().hex[:8]}"
    exp_req_str = json.dumps(msg.expense_request) if msg.expense_request else None

    conn.execute("""
        INSERT INTO messages (id, chat_type, sender_id, target_id, text, expense_request)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (mid, msg.chat_type, msg.sender_id, msg.target_id, msg.text, exp_req_str))

    user_row = conn.execute("SELECT name, avatar FROM users WHERE id = ?", (msg.sender_id,)).fetchone()
    conn.commit()
    conn.close()

    payload = {
        "id": mid,
        "chat_type": msg.chat_type,
        "sender_id": msg.sender_id,
        "target_id": msg.target_id,
        "sender_name": user_row["name"] if user_row else "Unknown",
        "sender_avatar": user_row["avatar"] if user_row else "",
        "text": msg.text,
        "expense_request": msg.expense_request,
        "timestamp": datetime.now().isoformat()
    }

    await manager.broadcast(payload)
    return {"status": "sent", "message": payload}

# --- ITINERARIES ---

@app.get("/api/squads/{squad_id}/itinerary")
def get_itineraries(squad_id: str):
    conn = get_db_connection()
    rows = conn.execute("SELECT i.*, u.name as creator_name FROM itineraries i JOIN users u ON i.created_by = u.id WHERE i.squad_id = ? ORDER BY i.date ASC, i.time ASC", (squad_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/squads/{squad_id}/itinerary")
def create_itinerary(squad_id: str, item: ItineraryCreate):
    conn = get_db_connection()
    iid = f"it_{uuid.uuid4().hex[:8]}"
    conn.execute("""
        INSERT INTO itineraries (id, squad_id, title, date, time, location, cost, votes, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (iid, squad_id, item.title, item.date, item.time, item.location, item.cost, item.created_by))
    conn.commit()
    conn.close()
    return {"status": "created", "itinerary_id": iid}

@app.post("/api/itinerary/{itinerary_id}/vote")
def vote_itinerary(itinerary_id: str):
    conn = get_db_connection()
    conn.execute("UPDATE itineraries SET votes = votes + 1 WHERE id = ?", (itinerary_id,))
    conn.commit()
    row = conn.execute("SELECT votes FROM itineraries WHERE id = ?", (itinerary_id,)).fetchone()
    conn.close()
    return {"status": "voted", "votes": row["votes"] if row else 1}

# --- OCR & AI VOICE PARSING ---

@app.post("/api/ocr/scan-receipt")
def scan_receipt(sample_text: Optional[str] = "Luigi Italian Bistro\nWoodfired Artisan Pizza $24.50\nCraft IPA Beer $16.00\nCaesar Salad $12.50\nSubtotal $53.00\nTax & Tip $9.00\nTOTAL $62.00"):
    parsed = parse_receipt_text(sample_text)
    return parsed

@app.get("/api/fx/rates")
def get_fx_rates():
    return EXCHANGE_RATES

@app.post("/api/voice/parse")
def parse_voice_command(req: VoiceParseRequest):
    text = req.voice_text.lower()

    title = "Voice Expense"
    amount = 25.0

    import re
    amounts = re.findall(r'\$?(\d+(?:\.\d{2})?)', text)
    if amounts:
        amount = float(amounts[0])

    if "coffee" in text:
        title = "Morning Squad Coffee ☕"
    elif "dinner" in text or "food" in text or "pizza" in text:
        title = "Squad Dinner 🍕"
    elif "groceries" in text:
        title = "Grocery Split 🥩"

    return {
        "parsed_title": title,
        "parsed_amount": amount,
        "original_text": req.voice_text
    }

@app.get("/api/analytics")
def get_analytics():
    conn = get_db_connection()
    expenses = conn.execute("SELECT category, amount FROM expenses WHERE category != 'Settlement'").fetchall()
    
    cat_map: Dict[str, float] = {}
    total_spent = 0.0
    for e in expenses:
        cat = e["category"]
        amt = e["amount"]
        cat_map[cat] = cat_map.get(cat, 0.0) + amt
        total_spent += amt

    conn.close()
    return {
        "total_spent": round(total_spent, 2),
        "categories": {cat: round(amt, 2) for cat, amt in cat_map.items()}
    }

# --- WEBSOCKET ---

@app.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Serve Frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
