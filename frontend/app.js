/**
 * SplitVibe Frontend Application Logic (Auth Enabled)
 * REST APIs, WebSockets, Auth (Login/Signup/Logout), Settings, Themes, Itineraries, OCR & Voice.
 */

const API_BASE = 'http://localhost:8000/api';
const WS_BASE = 'ws://localhost:8000/ws';

let users = [];
let squads = [];
let currentUser = null;
let activeChat = { type: 'group', id: 'sq1', name: 'Tahoe Ski Roadtrip 🏔️', avatar: '' };
let wsConnection = null;

document.addEventListener('DOMContentLoaded', async () => {
    initTabNavigation();
    initModals();
    initAuthSystem();
    initSettingsAndThemes();
    await loadInitialData();
    setupUserSwitcher();
});

// --- INITIALIZATION & USER SWITCHING ---

async function loadInitialData() {
    try {
        const usersRes = await fetch(`${API_BASE}/users`);
        users = await usersRes.json();
        
        const squadsRes = await fetch(`${API_BASE}/squads`);
        squads = await squadsRes.json();

        // Check localStorage for saved authenticated session
        const savedUserStr = localStorage.getItem('splitvibe_user');
        if (savedUserStr) {
            try {
                currentUser = JSON.parse(savedUserStr);
                // Verify user still exists in DB list
                const match = users.find(u => u.id === currentUser.id);
                if (match) currentUser = match;
            } catch (e) {
                currentUser = users[0];
            }
        } else {
            currentUser = users[0];
        }

        updateUserUI();

        loadFeed();
        loadSquads();
        loadItineraries(squads[0]?.id || 'sq1');
        loadDebtGraph(squads[0]?.id || 'sq1');
        loadAnalytics();
        initChatSystem();
        loadUserSettings();

    } catch (err) {
        console.error('Failed to load initial data:', err);
    }
}

function updateUserUI() {
    if (!currentUser) return;
    document.getElementById('current-user-avatar').src = currentUser.avatar;
    document.getElementById('current-user-name').textContent = currentUser.name;
    
    // Toggle Auth Buttons
    const openAuthBtn = document.getElementById('open-auth-btn');
    const logoutBtn = document.getElementById('logout-btn');

    const isLoggedIn = localStorage.getItem('splitvibe_user') !== null;
    if (isLoggedIn) {
        openAuthBtn?.classList.add('hidden');
        logoutBtn?.classList.remove('hidden');
    } else {
        openAuthBtn?.classList.remove('hidden');
        logoutBtn?.classList.add('hidden');
    }

    connectWebSocket();
}

function setupUserSwitcher() {
    const btn = document.getElementById('user-switcher-btn');
    const dropdown = document.getElementById('user-menu-dropdown');

    btn.addEventListener('click', () => {
        dropdown.classList.toggle('hidden');
    });

    dropdown.innerHTML = users.map(u => `
        <div class="user-option" onclick="switchUser('${u.id}')">
            <img src="${u.avatar}" alt="${u.name}">
            <div>
                <div style="font-size:0.85rem; font-weight:600;">${u.name}</div>
                <div style="font-size:0.75rem; color:var(--text-muted);">${u.handle}</div>
            </div>
        </div>
    `).join('');
}

window.switchUser = function(userId) {
    currentUser = users.find(u => u.id === userId);
    localStorage.setItem('splitvibe_user', JSON.stringify(currentUser));
    updateUserUI();
    document.getElementById('user-menu-dropdown').classList.add('hidden');
    loadChatMessages();
    loadUserSettings();
};

// --- AUTH SYSTEM (LOGIN / SIGNUP / LOGOUT) ---

function initAuthSystem() {
    const openAuthBtn = document.getElementById('open-auth-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const authModal = document.getElementById('auth-modal');

    const tabLogin = document.getElementById('auth-tab-login');
    const tabSignup = document.getElementById('auth-tab-signup');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const errorBanner = document.getElementById('auth-error-banner');

    openAuthBtn?.addEventListener('click', () => {
        errorBanner.classList.add('hidden');
        authModal.classList.remove('hidden');
    });

    logoutBtn?.addEventListener('click', () => {
        localStorage.removeItem('splitvibe_user');
        currentUser = users[0];
        updateUserUI();
        alert('You have logged out.');
    });

    tabLogin?.addEventListener('click', () => {
        tabLogin.classList.add('active');
        tabSignup.classList.remove('active');
        loginForm.classList.remove('hidden');
        signupForm.classList.add('hidden');
        errorBanner.classList.add('hidden');
    });

    tabSignup?.addEventListener('click', () => {
        tabSignup.classList.add('active');
        tabLogin.classList.remove('active');
        signupForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
        errorBanner.classList.add('hidden');
    });

    // Handle Login Submit
    loginForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const handle = document.getElementById('login-handle').value;
        const password = document.getElementById('login-password').value;

        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ handle, password })
            });

            const data = await res.json();
            if (!res.ok) {
                errorBanner.textContent = data.detail || 'Login failed';
                errorBanner.classList.remove('hidden');
                return;
            }

            currentUser = data.user;
            localStorage.setItem('splitvibe_user', JSON.stringify(currentUser));
            updateUserUI();
            authModal.classList.add('hidden');

            alert(`Welcome back, ${currentUser.name}! 🚀`);

        } catch (err) {
            errorBanner.textContent = 'Server communication error';
            errorBanner.classList.remove('hidden');
        }
    });

    // Handle Signup Submit
    signupForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('signup-name').value;
        const handle = document.getElementById('signup-handle').value;
        const avatar = document.getElementById('signup-avatar').value || undefined;
        const bio = document.getElementById('signup-bio').value || undefined;
        const password = document.getElementById('signup-password').value;

        try {
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, handle, avatar, bio, password })
            });

            const data = await res.json();
            if (!res.ok) {
                errorBanner.textContent = data.detail || 'Registration failed';
                errorBanner.classList.remove('hidden');
                return;
            }

            currentUser = data.user;
            localStorage.setItem('splitvibe_user', JSON.stringify(currentUser));
            
            // Refresh users list
            const usersRes = await fetch(`${API_BASE}/users`);
            users = await usersRes.json();

            updateUserUI();
            setupUserSwitcher();
            authModal.classList.add('hidden');

            alert(`Account created! Welcome to SplitVibe, ${currentUser.name}! 🎉`);

        } catch (err) {
            errorBanner.textContent = 'Server communication error';
            errorBanner.classList.remove('hidden');
        }
    });
}

// --- NAVIGATION TABS ---

function initTabNavigation() {
    const navBtns = document.querySelectorAll('.nav-btn');
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            navBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

// --- TAB 1: SOCIAL FEED & REELS ---

async function loadFeed(filterType = null) {
    const container = document.getElementById('feed-container');
    container.innerHTML = '<div style="color:var(--text-muted);">Loading posts...</div>';

    try {
        let url = `${API_BASE}/posts`;
        if (filterType) url += `?post_type=${filterType}`;

        const res = await fetch(url);
        const posts = await res.json();

        if (posts.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted);">No posts yet! Share a squad moment.</div>';
            return;
        }

        container.innerHTML = posts.map(p => {
            const isReel = p.type === 'reel';
            return `
                <div class="glass-card post-card">
                    <div class="post-header">
                        <img class="post-avatar" src="${p.user?.avatar || ''}" alt="Avatar">
                        <div class="post-user-info">
                            <h4>${p.user?.name || 'Squad Member'}</h4>
                            <span>${p.squad_name ? p.squad_name : 'Public Memory'} • ${new Date(p.created_at).toLocaleDateString()}</span>
                        </div>
                    </div>

                    <div class="post-media-container">
                        ${isReel ? `
                            <video src="${p.media_url}" autoplay loop muted playsinline></video>
                            <span class="reel-badge"><i class="fa-solid fa-play"></i> Reel</span>
                        ` : `
                            <img src="${p.media_url}" alt="Post Media">
                        `}
                    </div>

                    <p class="post-caption">${p.caption}</p>

                    <div class="post-actions">
                        <button class="action-btn" onclick="likePost('${p.id}', this)">
                            <i class="fa-regular fa-heart"></i>
                            <span>${p.likes} Likes</span>
                        </button>
                        <button class="action-btn" onclick="toggleComments('${p.id}')">
                            <i class="fa-regular fa-comment"></i>
                            <span>${p.comments?.length || 0} Comments</span>
                        </button>
                    </div>

                    <div class="comments-drawer hidden" id="comments-${p.id}" style="margin-top:10px; font-size:0.85rem;">
                        <div class="comments-list" style="display:flex; flex-direction:column; gap:6px; margin-bottom:8px;">
                            ${(p.comments || []).map(c => `
                                <div style="background:rgba(255,255,255,0.05); padding:6px 10px; border-radius:8px;">
                                    <strong style="color:var(--accent-cyan);">${c.name}:</strong> ${c.text}
                                </div>
                            `).join('')}
                        </div>
                        <div style="display:flex; gap:6px;">
                            <input type="text" id="comment-input-${p.id}" placeholder="Write a comment..." style="flex:1; background:rgba(255,255,255,0.05); border:1px solid var(--border-color); border-radius:6px; padding:4px 8px; color:var(--text-primary);">
                            <button class="btn btn-sm btn-primary" onclick="addComment('${p.id}')">Post</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (err) {
        console.error('Failed to load feed:', err);
    }
}

document.getElementById('filter-all-posts')?.addEventListener('click', (e) => {
    setActiveFilterBtn(e.target);
    loadFeed();
});
document.getElementById('filter-photos')?.addEventListener('click', (e) => {
    setActiveFilterBtn(e.target);
    loadFeed('photo');
});
document.getElementById('filter-reels')?.addEventListener('click', (e) => {
    setActiveFilterBtn(e.target);
    loadFeed('reel');
});

function setActiveFilterBtn(btn) {
    document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

window.likePost = async function(postId, btnEl) {
    try {
        const res = await fetch(`${API_BASE}/posts/${postId}/like`, { method: 'POST' });
        const data = await res.json();
        const icon = btnEl.querySelector('i');
        icon.className = 'fa-solid fa-heart';
        icon.style.color = 'var(--accent-rose)';
        btnEl.querySelector('span').textContent = `${data.likes} Likes`;
    } catch (err) {
        console.error(err);
    }
};

window.toggleComments = function(postId) {
    document.getElementById(`comments-${postId}`).classList.toggle('hidden');
};

window.addComment = async function(postId) {
    const input = document.getElementById(`comment-input-${postId}`);
    const text = input.value.trim();
    if (!text) return;

    try {
        await fetch(`${API_BASE}/posts/${postId}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id, text })
        });
        input.value = '';
        loadFeed();
    } catch (err) {
        console.error(err);
    }
};

// --- TAB 2: CHATS & MESSAGES ---

function initChatSystem() {
    renderChatSidebar();
    loadChatMessages();

    document.getElementById('chat-send-btn').addEventListener('click', sendChatMessage);
    document.getElementById('chat-text-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });

    document.getElementById('chat-quick-bill-btn').addEventListener('click', sendBillRequestInChat);
    document.getElementById('chat-voice-btn').addEventListener('click', triggerVoiceSplit);
}

function renderChatSidebar() {
    const squadListEl = document.getElementById('squad-channels-list');
    const directListEl = document.getElementById('direct-chats-list');

    squadListEl.innerHTML = squads.map(s => `
        <div class="chat-item ${activeChat.type === 'group' && activeChat.id === s.id ? 'active' : ''}" onclick="selectChat('group', '${s.id}', '${s.name}', '${s.avatar}')">
            <img src="${s.avatar}" alt="Squad">
            <div class="chat-item-name">${s.name}</div>
        </div>
    `).join('');

    const otherUsers = users.filter(u => u.id !== currentUser?.id);
    directListEl.innerHTML = otherUsers.map(u => `
        <div class="chat-item ${activeChat.type === 'direct' && activeChat.id === u.id ? 'active' : ''}" onclick="selectChat('direct', '${u.id}', '${u.name}', '${u.avatar}')">
            <img src="${u.avatar}" alt="User">
            <div class="chat-item-name">${u.name}</div>
        </div>
    `).join('');
}

window.selectChat = function(type, id, name, avatar) {
    activeChat = { type, id, name, avatar };
    renderChatSidebar();

    document.getElementById('chat-target-avatar').src = avatar;
    document.getElementById('chat-target-name').textContent = name;
    document.getElementById('chat-target-status').textContent = type === 'group' ? 'Group Channel' : 'Direct Message';

    loadChatMessages();
};

async function loadChatMessages() {
    if (!currentUser) return;
    const container = document.getElementById('chat-messages-container');

    try {
        let url = `${API_BASE}/messages?chat_type=${activeChat.type}&target_id=${activeChat.id}&sender_id=${currentUser.id}`;
        const res = await fetch(url);
        const messages = await res.json();

        if (messages.length === 0) {
            container.innerHTML = `
                <div class="chat-empty-state">
                    <i class="fa-solid fa-comments"></i>
                    <p>No messages yet in ${activeChat.name}. Say hi!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = messages.map(m => {
            const isMe = m.sender_id === currentUser.id;
            return `
                <div class="msg-bubble ${isMe ? 'sent' : 'received'}">
                    ${!isMe ? `<div class="msg-sender">${m.sender_name}</div>` : ''}
                    <div>${m.text}</div>
                    ${m.expense_request ? `
                        <div class="bill-request-card">
                            <div class="bill-request-title"><i class="fa-solid fa-receipt"></i> Bill Split Request</div>
                            <div>${m.expense_request.title}</div>
                            <strong style="color:#fff;">$${m.expense_request.amount?.toFixed(2)}</strong>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');

        container.scrollTop = container.scrollHeight;

    } catch (err) {
        console.error('Failed to load chat messages:', err);
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chat-text-input');
    const text = input.value.trim();
    if (!text || !currentUser) return;

    try {
        await fetch(`${API_BASE}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_type: activeChat.type,
                sender_id: currentUser.id,
                target_id: activeChat.id,
                text: text
            })
        });

        input.value = '';
        loadChatMessages();

    } catch (err) {
        console.error('Failed to send message:', err);
    }
}

async function sendBillRequestInChat() {
    const title = prompt('Expense title to request in chat:', 'Squad Coffee ☕');
    if (!title) return;
    const amountStr = prompt('Amount to split ($):', '25.00');
    if (!amountStr) return;

    const amount = parseFloat(amountStr);

    try {
        await fetch(`${API_BASE}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_type: activeChat.type,
                sender_id: currentUser.id,
                target_id: activeChat.id,
                text: `Split request: ${title}`,
                expense_request: { title, amount }
            })
        });

        loadChatMessages();
    } catch (err) {
        console.error(err);
    }
}

async function triggerVoiceSplit() {
    const voiceText = prompt('Speak or type voice command:', 'Split $80 dinner between Alex and Maya');
    if (!voiceText) return;

    try {
        const res = await fetch(`${API_BASE}/voice/parse`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ voice_text: voiceText })
        });
        const parsed = await res.json();

        document.getElementById('exp-title-input').value = parsed.parsed_title;
        document.getElementById('exp-amount-input').value = parsed.parsed_amount;
        document.getElementById('add-expense-modal').classList.remove('hidden');

    } catch (err) {
        console.error(err);
    }
}

function connectWebSocket() {
    if (!currentUser) return;
    if (wsConnection) wsConnection.close();

    wsConnection = new WebSocket(`${WS_BASE}/chat/${currentUser.id}`);
    wsConnection.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.target_id === activeChat.id || msg.sender_id === activeChat.id) {
            loadChatMessages();
        }
    };
}

// --- TAB 3: SQUADS & EXPENSES ---

async function loadSquads() {
    const container = document.getElementById('squads-container');
    container.innerHTML = squads.map(s => `
        <div class="glass-card squad-card" onclick="viewSquadDetail('${s.id}')">
            <img class="squad-card-img" src="${s.avatar}" alt="${s.name}">
            <div class="squad-card-title">${s.name}</div>
            <div style="font-size:0.85rem; color:var(--text-muted);">${s.description}</div>
            <div class="squad-members-avatars">
                ${(s.members || []).map(m => `<img src="${m.avatar}" alt="${m.name}">`).join('')}
            </div>
        </div>
    `).join('');
}

window.viewSquadDetail = async function(squadId) {
    const squad = squads.find(s => s.id === squadId);
    if (!squad) return;

    document.getElementById('squads-container').classList.add('hidden');
    const detailSection = document.getElementById('squad-detail-container');
    detailSection.classList.remove('hidden');
    document.getElementById('selected-squad-title').textContent = `${squad.name} — Expenses`;

    try {
        const res = await fetch(`${API_BASE}/squads/${squadId}/summary`);
        const summary = await res.json();

        const listEl = document.getElementById('squad-expenses-list');
        listEl.innerHTML = summary.expenses.map(e => {
            const payer = users.find(u => u.id === e.paid_by);
            return `
                <div class="glass-card" style="margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; gap:12px; align-items:center;">
                        ${e.memory_photo ? `<img src="${e.memory_photo}" style="width:50px; height:50px; border-radius:8px; object-fit:cover;">` : ''}
                        <div>
                            <div style="font-weight:700; font-size:1rem;">${e.title}</div>
                            <div style="font-size:0.8rem; color:var(--text-muted);">Paid by ${payer?.name || e.paid_by} • ${e.category} • ${e.date}</div>
                        </div>
                    </div>
                    <div style="font-family:var(--font-heading); font-size:1.2rem; font-weight:700; color:var(--accent-emerald);">
                        $${e.amount.toFixed(2)}
                    </div>
                </div>
            `;
        }).join('');

    } catch (err) {
        console.error(err);
    }
};

document.getElementById('back-to-squads-btn')?.addEventListener('click', () => {
    document.getElementById('squad-detail-container').classList.add('hidden');
    document.getElementById('squads-container').classList.remove('hidden');
});

// --- TAB 4: ITINERARIES ---

async function loadItineraries(squadId) {
    const selectEl = document.getElementById('itinerary-squad-select');
    selectEl.innerHTML = squads.map(s => `<option value="${s.id}" ${s.id === squadId ? 'selected' : ''}>${s.name}</option>`).join('');

    selectEl.onchange = (e) => loadItineraries(e.target.value);

    const container = document.getElementById('itinerary-cards-container');
    container.innerHTML = '<div style="color:var(--text-muted);">Loading itinerary events...</div>';

    try {
        const res = await fetch(`${API_BASE}/squads/${squadId}/itinerary`);
        const items = await res.json();

        if (items.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted);">No events planned for this squad yet.</div>';
            return;
        }

        container.innerHTML = items.map(item => `
            <div class="glass-card itinerary-card">
                <div>
                    <div class="itin-header">
                        <span class="itin-date-badge">${item.date} • ${item.time}</span>
                        <strong style="color:var(--accent-emerald); font-size:0.9rem;">$${item.cost?.toFixed(2)} / person</strong>
                    </div>
                    <h3 style="font-size:1.1rem; margin:6px 0;">${item.title}</h3>
                    <p style="font-size:0.85rem; color:var(--text-muted);"><i class="fa-solid fa-location-dot"></i> ${item.location || 'Squad Location'}</p>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:14px; border-top:1px solid var(--border-color); padding-top:10px;">
                    <span style="font-size:0.8rem; color:var(--text-muted);">Added by ${item.creator_name}</span>
                    <button class="btn btn-sm btn-outline" onclick="voteItinerary('${item.id}', this)">
                        <i class="fa-solid fa-thumbs-up"></i> <span>${item.votes} Votes</span>
                    </button>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error('Failed to load itineraries:', err);
    }
}

window.voteItinerary = async function(id, btnEl) {
    try {
        const res = await fetch(`${API_BASE}/itinerary/${id}/vote`, { method: 'POST' });
        const data = await res.json();
        btnEl.querySelector('span').textContent = `${data.votes} Votes`;
    } catch (err) {
        console.error(err);
    }
};

// --- TAB 5: DEBT GRAPH MINIMIZER ---

async function loadDebtGraph(squadId) {
    const selectEl = document.getElementById('settle-squad-select');
    selectEl.innerHTML = squads.map(s => `<option value="${s.id}" ${s.id === squadId ? 'selected' : ''}>${s.name}</option>`).join('');

    selectEl.onchange = (e) => loadDebtGraph(e.target.value);

    try {
        const res = await fetch(`${API_BASE}/squads/${squadId}/summary`);
        const summary = await res.json();

        const balancesEl = document.getElementById('net-balances-list');
        balancesEl.innerHTML = Object.entries(summary.net_balances).map(([uid, amt]) => {
            const user = users.find(u => u.id === uid);
            const isPos = amt >= 0;
            return `
                <div class="balance-item">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <img src="${user?.avatar}" style="width:28px; height:28px; border-radius:50%;">
                        <span>${user?.name || uid}</span>
                    </div>
                    <span class="balance-amount ${isPos ? 'positive' : 'negative'}">
                        ${isPos ? '+' : ''}$${amt.toFixed(2)}
                    </span>
                </div>
            `;
        }).join('');

        const settlementsEl = document.getElementById('simplified-settlements-list');
        if (summary.simplified_debts.length === 0) {
            settlementsEl.innerHTML = '<div style="color:var(--accent-emerald); font-weight:600; padding:10px 0;">🎉 Everyone is completely settled up!</div>';
            return;
        }

        settlementsEl.innerHTML = summary.simplified_debts.map(d => {
            const fromUser = users.find(u => u.id === d.from_user);
            const toUser = users.find(u => u.id === d.to_user);

            return `
                <div class="settlement-card-item">
                    <div class="settle-flow">
                        <span>${fromUser?.name}</span>
                        <i class="fa-solid fa-arrow-right-long"></i>
                        <span>${toUser?.name}</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:10px;">
                        <strong style="color:var(--accent-amber); font-size:1.1rem;">$${d.amount.toFixed(2)}</strong>
                        <button class="btn btn-sm btn-primary" onclick="settleDebt('${squadId}', '${d.from_user}', '${d.to_user}', ${d.amount})">
                            Settle Up
                        </button>
                    </div>
                </div>
            `;
        }).join('');

    } catch (err) {
        console.error('Failed to load debt graph:', err);
    }
}

window.settleDebt = async function(squadId, fromUser, toUser, amount) {
    try {
        await fetch(`${API_BASE}/expenses/settle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ squad_id: squadId, from_user: fromUser, to_user: toUser, amount: amount })
        });
        alert('Payment logged & debt settled!');
        loadDebtGraph(squadId);
        loadAnalytics();
    } catch (err) {
        console.error(err);
    }
};

// --- TAB 6: ANALYTICS ---

async function loadAnalytics() {
    try {
        const res = await fetch(`${API_BASE}/analytics`);
        const data = await res.json();

        document.getElementById('stat-total-spent').textContent = `$${data.total_spent.toFixed(2)}`;
        document.getElementById('stat-active-groups').textContent = squads.length;

        const container = document.getElementById('category-bars-container');
        const maxVal = Math.max(...Object.values(data.categories), 1);

        container.innerHTML = Object.entries(data.categories).map(([cat, amt]) => {
            const pct = (amt / maxVal) * 100;
            return `
                <div class="cat-bar-item">
                    <div class="cat-bar-header">
                        <span>${cat}</span>
                        <strong>$${amt.toFixed(2)}</strong>
                    </div>
                    <div class="cat-bar-bg">
                        <div class="cat-bar-fill" style="width: ${pct}%;"></div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (err) {
        console.error('Failed to load analytics:', err);
    }
}

// --- TAB 7: SETTINGS & THEMES ---

async function loadUserSettings() {
    if (!currentUser) return;

    document.getElementById('setting-name-input').value = currentUser.name;
    document.getElementById('setting-handle-input').value = currentUser.handle;
    document.getElementById('setting-avatar-input').value = currentUser.avatar;
    document.getElementById('setting-bio-input').value = currentUser.bio || '';
    document.getElementById('setting-venmo-input').value = currentUser.venmo_handle || '';
    document.getElementById('setting-zelle-input').value = currentUser.zelle_handle || '';

    try {
        const res = await fetch(`${API_BASE}/users/${currentUser.id}/settings`);
        const settings = await res.json();

        applyTheme(settings.theme || 'deep-space');

        document.getElementById('notify-expenses-toggle').checked = !!settings.notify_expenses;
        document.getElementById('notify-settlements-toggle').checked = !!settings.notify_settlements;
        document.getElementById('notify-chat-toggle').checked = !!settings.notify_chat;
        document.getElementById('notify-likes-toggle').checked = !!settings.notify_likes;

    } catch (err) {
        console.error('Failed to load settings:', err);
    }
}

function initSettingsAndThemes() {
    document.querySelectorAll('.theme-option-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.theme-option-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            const themeName = card.getAttribute('data-theme-name');
            applyTheme(themeName);
        });
    });

    document.getElementById('profile-update-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('setting-name-input').value;
        const handle = document.getElementById('setting-handle-input').value;
        const avatar = document.getElementById('setting-avatar-input').value;
        const bio = document.getElementById('setting-bio-input').value;
        const venmo_handle = document.getElementById('setting-venmo-input').value;
        const zelle_handle = document.getElementById('setting-zelle-input').value;

        try {
            await fetch(`${API_BASE}/users/${currentUser.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, handle, avatar, bio, venmo_handle, zelle_handle })
            });

            currentUser.name = name;
            currentUser.handle = handle;
            currentUser.avatar = avatar;
            currentUser.bio = bio;
            updateUserUI();

            alert('Profile updated successfully!');
        } catch (err) {
            console.error(err);
        }
    });

    document.getElementById('save-settings-btn')?.addEventListener('click', async () => {
        const activeThemeCard = document.querySelector('.theme-option-card.active');
        const theme = activeThemeCard ? activeThemeCard.getAttribute('data-theme-name') : 'deep-space';

        const notify_expenses = document.getElementById('notify-expenses-toggle').checked;
        const notify_settlements = document.getElementById('notify-settlements-toggle').checked;
        const notify_chat = document.getElementById('notify-chat-toggle').checked;
        const notify_likes = document.getElementById('notify-likes-toggle').checked;

        try {
            await fetch(`${API_BASE}/users/${currentUser.id}/settings`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ theme, notify_expenses, notify_settlements, notify_chat, notify_likes })
            });

            alert('Settings saved successfully!');
        } catch (err) {
            console.error(err);
        }
    });
}

function applyTheme(themeName) {
    document.body.setAttribute('data-theme', themeName);
    document.querySelectorAll('.theme-option-card').forEach(card => {
        if (card.getAttribute('data-theme-name') === themeName) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });
}

// --- MODALS ---

function initModals() {
    const addExpBtn = document.getElementById('open-add-expense-modal');
    const expModal = document.getElementById('add-expense-modal');

    addExpBtn?.addEventListener('click', () => {
        populateExpenseModalFields();
        expModal.classList.remove('hidden');
    });

    const addPostBtn = document.getElementById('open-create-post-modal');
    const postModal = document.getElementById('create-post-modal');

    addPostBtn?.addEventListener('click', () => {
        populatePostModalFields();
        postModal.classList.remove('hidden');
    });

    const ocrBtn = document.getElementById('open-ocr-modal');
    const ocrModal = document.getElementById('ocr-modal');
    ocrBtn?.addEventListener('click', () => ocrModal.classList.remove('hidden'));

    const processOcrBtn = document.getElementById('process-ocr-btn');
    processOcrBtn?.addEventListener('click', async () => {
        const text = document.getElementById('ocr-sample-text').value;
        const res = await fetch(`${API_BASE}/ocr/scan-receipt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sample_text: text })
        });
        const parsed = await res.json();
        
        const container = document.getElementById('ocr-results-container');
        container.innerHTML = `
            <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; font-size:0.85rem;">
                <strong>Extracted Items:</strong>
                ${parsed.items.map(item => `<div style="display:flex; justify-content:space-between; margin-top:4px;"><span>${item.name}</span><strong>$${item.price.toFixed(2)}</strong></div>`).join('')}
                <div style="border-top:1px solid var(--border-color); margin-top:8px; padding-top:6px; display:flex; justify-content:space-between; color:var(--accent-emerald);">
                    <strong>Calculated Total:</strong>
                    <strong>$${parsed.total.toFixed(2)}</strong>
                </div>
            </div>
            <button class="btn btn-sm btn-primary" style="margin-top:10px; width:100%;" onclick="useOcrInExpense(${parsed.total})">Use Total in Expense Modal</button>
        `;
    });

    const addItinBtn = document.getElementById('open-add-itinerary-modal');
    const itinModal = document.getElementById('add-itinerary-modal');
    addItinBtn?.addEventListener('click', () => {
        document.getElementById('itin-squad-select').innerHTML = squads.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
        itinModal.classList.remove('hidden');
    });

    document.querySelectorAll('.close-modal-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            expModal.classList.add('hidden');
            postModal.classList.add('hidden');
            ocrModal.classList.add('hidden');
            itinModal.classList.add('hidden');
            document.getElementById('auth-modal')?.classList.add('hidden');
        });
    });

    document.getElementById('add-expense-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const squad_id = document.getElementById('exp-squad-select').value;
        const paid_by = document.getElementById('exp-paidby-select').value;
        const title = document.getElementById('exp-title-input').value;
        const amount = parseFloat(document.getElementById('exp-amount-input').value);
        const currency = document.getElementById('exp-currency-select').value;
        const category = document.getElementById('exp-category-select').value;
        const memory_photo = document.getElementById('exp-photo-input').value || null;

        const squad = squads.find(s => s.id === squad_id);
        const members = squad?.members || users;
        const splitPerPerson = amount / members.length;
        const splits = {};
        members.forEach(m => splits[m.id] = splitPerPerson);

        try {
            await fetch(`${API_BASE}/expenses`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ squad_id, paid_by, title, amount, currency, category, splits, memory_photo })
            });

            expModal.classList.add('hidden');
            alert('Expense added successfully!');
            loadDebtGraph(squad_id);
            loadFeed();
            loadAnalytics();
        } catch (err) {
            console.error(err);
        }
    });

    document.getElementById('create-post-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const type = document.getElementById('post-type-select').value;
        const caption = document.getElementById('post-caption-input').value;
        const media_url = document.getElementById('post-media-input').value;
        const squad_id = document.getElementById('post-squad-select').value || null;

        try {
            await fetch(`${API_BASE}/posts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: currentUser.id, squad_id, caption, media_url, type })
            });

            postModal.classList.add('hidden');
            loadFeed();
        } catch (err) {
            console.error(err);
        }
    });

    document.getElementById('add-itinerary-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const squad_id = document.getElementById('itin-squad-select').value;
        const title = document.getElementById('itin-title-input').value;
        const date = document.getElementById('itin-date-input').value;
        const time = document.getElementById('itin-time-input').value;
        const location = document.getElementById('itin-location-input').value;
        const cost = parseFloat(document.getElementById('itin-cost-input').value || 0);

        try {
            await fetch(`${API_BASE}/squads/${squad_id}/itinerary`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ squad_id, title, date, time, location, cost, created_by: currentUser.id })
            });

            itinModal.classList.add('hidden');
            loadItineraries(squad_id);
        } catch (err) {
            console.error(err);
        }
    });
}

window.useOcrInExpense = function(total) {
    document.getElementById('ocr-modal').classList.add('hidden');
    document.getElementById('exp-amount-input').value = total;
    populateExpenseModalFields();
    document.getElementById('add-expense-modal').classList.remove('hidden');
};

function populateExpenseModalFields() {
    const squadSelect = document.getElementById('exp-squad-select');
    const userSelect = document.getElementById('exp-paidby-select');

    squadSelect.innerHTML = squads.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
    userSelect.innerHTML = users.map(u => `<option value="${u.id}" ${u.id === currentUser?.id ? 'selected' : ''}>${u.name}</option>`).join('');
}

function populatePostModalFields() {
    const squadSelect = document.getElementById('post-squad-select');
    squadSelect.innerHTML = '<option value="">No Squad Tag</option>' + squads.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
}
