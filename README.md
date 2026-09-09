# ⚡ SplitVibe — Social Group Expense & Memory Platform

**SplitVibe** is a hybrid social finance platform that combines **photo memories**, **short video reels**, **real-time 1-on-1 & group chat**, **itemized expense splitting**, and **graph debt simplification** into a unified web ecosystem.

---

## 🔥 Key Features

- **📸 Social Activity, Photos & Reels**: Share squad moments as photos or video reels with likes, comments, and expense tags.
- **💬 Real-Time Messaging**: Direct messaging and squad channels with instant WebSocket broadcasts & in-chat bill split requests.
- **⚖️ Graph Debt Minimizer**: Greedy net-balance algorithm that simplifies transitive group debts into minimal direct settlements.
- **🧾 AI Receipt OCR Scanner**: Scan or paste paper receipts to extract line items and split bill costs item-by-item.
- **✈️ Squad Trip Itinerary**: Collaborative trip scheduler for activities, flight bookings, and squad voting.
- **⚙️ Settings & Customization**: Dynamic theme engine (**Deep Space**, **Cyberpunk**, **Emerald**, **Light**) and profile/notification controls.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, SQLite, WebSockets.
- **Frontend**: Modern SPA (HTML5, Vanilla CSS3 Glassmorphism, JavaScript, FontAwesome, Google Fonts).

---

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Backend Server**:
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

3. **Access Application**:
   Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🧪 Running Automated Tests

```bash
python backend/test_api.py
```
