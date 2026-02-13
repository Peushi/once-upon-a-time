# Enchantext
### *"Cast your own adventure"* 🪄

Enchantext is a **Choose Your Own Adventure** web application where readers explore branching interactive stories and authors design dynamic narrative paths.

This project was developed as a **Final Project – Django & Flask**, implementing a split architecture between a Flask REST API and a Django web application.

---

## ✨ Core Concept

- **Authors** create interactive stories made of pages and choices
- **Readers** play stories by selecting choices and reaching endings
- The system tracks gameplay statistics and player history

---

## 🧱 Architecture

This application follows a **two-app design**:

| Component | Responsibility |
|-----------|----------------|
| **Flask API** (port 5000) | Story content storage (stories, pages, choices) |
| **Django App** (port 8000) | UI, gameplay engine, authentication, tracking |

**Important separation:**

✅ Story content → Flask DB (`site.db`)
✅ Gameplay & user data → Django DB (`db.sqlite3`)

```
Browser → Django (8000) → Flask API (5000) → SQLite
                ↓
           Django DB
```

---

## 🛠️ Tech Stack

**Backend**
- Django 5.x
- Flask 3.x
- SQLite
- SQLAlchemy

**Frontend**
- HTML Templates
- CSS (Pastel Glassmorphism Theme)
- Fredoka Font
- Vis Network (Story Tree Visualization)

**Other**
- REST API with API Key Authentication
- Git / GitHub

---

## 🚀 Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/Peushi/once-upon-a-time.git
cd once-upon-a-time
```

---

### 2️⃣ Environment Variables

Create a `.env` file in **`flask-api/`**:

```
API_KEY=nahb-secret-api-key-2026
DATABASE_URL=sqlite:///site.db
```

Create a `.env` file in **`django-app/`**:

```
FLASK_API_URL=http://localhost:5000
FLASK_API_KEY=nahb-secret-api-key-2026
SECRET_KEY=django-dev-secret-2026
DEBUG=True
```

---

### 3️⃣ Flask API Setup

```bash
cd flask-api

python -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows

pip install -r requirements.txt
python app.py
```

Flask runs on: 👉 http://127.0.0.1:5000

---

### 4️⃣ Django Setup

Open a **second terminal**:

```bash
cd django-app

python -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Django runs on: 👉 http://127.0.0.1:8000

---

## ⚠️ Important

Both servers must be running **simultaneously**:

| Server | Port | Role |
|--------|------|------|
| Flask | 5000 | Story Engine API |
| Django | 8000 | UI & Gameplay |

---

## 🔑 Test Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin (full access) |
| author1 | test1234 | Author |
| reader1 | test1234 | Reader |

To create your own admin account:

```bash
cd django-app
python manage.py createsuperuser
```

---

## 🔌 Flask API Endpoints

### Public (no authentication required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stories` | List stories (filter: `status`, `tags`, `search`) |
| GET | `/stories/<id>` | Get single story |
| GET | `/stories/<id>/start` | Get start page ID |
| GET | `/pages/<id>` | Get page + choices |

### Protected (requires `X-API-KEY` header)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/stories` | Create story |
| PUT | `/stories/<id>` | Update story |
| DELETE | `/stories/<id>` | Delete story |
| POST | `/stories/<id>/pages` | Create page |
| PUT | `/pages/<id>` | Update page |
| DELETE | `/pages/<id>` | Delete page |
| POST | `/pages/<id>/choices` | Create choice |
| PUT | `/choices/<id>` | Update choice |
| DELETE | `/choices/<id>` | Delete choice |

---

## ✨ Features

### 📖 Reader Side
- Browse published stories
- Search & filter by title / tags
- Play interactive branching stories
- Multiple named endings
- Auto-save progression (resume later)
- Personal play history
- Rate stories (1–5 stars)
- Report inappropriate content

### ✍️ Author Side
- Create & edit stories
- Draft / Published / Suspended states
- Add and manage pages
- Add branching choices
- Set start page
- Preview stories (excluded from statistics)
- Story Tree Visualization 📊

### 🛡️ Admin / Moderation
- Global statistics dashboard
- Suspend / unsuspend stories
- View and manage reports
- Full access to all stories

---

## 📊 Story Tree Visualization

Authors can view a graphical map of their story structure:

- Displays all branching paths
- Highlights the start page and endings
- Interactive drag & zoom layout
- Hierarchical graph view

Powered by **[Vis Network](https://visjs.github.io/vis-network/docs/network/)**

---

## 👥 Roles & Permissions

| Action | Reader | Author | Admin |
|--------|--------|--------|-------|
| Browse published stories | ✅ | ✅ | ✅ |
| Play stories | ✅ | ✅ | ✅ |
| View play history | ✅ | ✅ | ✅ |
| Rate stories | ✅ | ✅ | ✅ |
| Report stories | ✅ | ✅ | ✅ |
| Create stories | ❌ | ✅ | ✅ |
| Edit own stories | ❌ | ✅ | ✅ |
| Edit any story | ❌ | ❌ | ✅ |
| Suspend stories | ❌ | ❌ | ✅ |
| View global stats | ❌ | ❌ | ✅ |
| Manage reports | ❌ | ❌ | ✅ |

---

## 🎨 UI / Design

The interface uses:
- Soft pastel colour palette
- Glassmorphism cards
- Rounded playful elements
- **Fredoka** font
- Smooth hover animations

---

## 👥 Contributors

- **Peushi Ariyawansa**
- **Karma Soliman**

---

## 📜 Academic Context

Developed for:
**Final Project – Django & Flask**
EPITA – Computer Science Program