# ♻️ Smart Waste Management System

**B.Tech Final Year Project**  
Team: Aniket, Pratigya, and Arul

A web-based platform with three separate portals — Citizen, Admin, and Collection Staff — all backed by the same MySQL database with strict role-based access control.

---

## Portals

| Portal | URL | Who uses it | Account creation |
|---|---|---|---|
| 🏠 Landing | `/` | Everyone | — |
| 👤 Citizen | `/citizen/*` | Public users | Self-registration |
| 🏛️ Admin | `/admin/*` | Administrators | `python create_admin.py` |
| 🚛 Staff | `/staff/*` | Collection team | Created by an admin |

---

## Project Workflow

```
Citizen                          System                         Admin / Staff
  │                                 │                              │
  ├─ Visits landing page (/)        │                              │
  ├─ Registers / Logs in            │                              │
  │   (/citizen/register, /login)   │                              │
  │                                 │                              │
  ├─ Reports waste ────────────────►│                              │
  │   (description, category,       ├─ Validates input             │
  │    location, photo)             ├─ Saves image (UUID name)     │
  │                                 ├─ Generates WMS-YYYYMMDD-XXXX │
  │◄────── Complaint ID ────────────┤ ├─ Saves to MySQL            │
  │                                 │                              │
  │                                 │◄────── Admin logs in ────────┤
  │                                 │◄────── Views all complaints ─┤
  │                                 │◄────── Assigns staff member ─┤
  │                                 │◄────── Updates status ───────┤
  │                                 │                              │
  │                                 │◄────── Staff logs in ────────┤
  │                                 │◄────── Views their tasks ────┤
  │                                 │◄──── Marks In Progress ──────┤
  │                                 │◄── Uploads after-photo ──────┤
  │                                 │◄────── Marks Resolved ───────┤
  │                                 │                              │
  │                                 ├─ Awards 10 Green Points      │
  │◄────── +10 🌿 Green Points ─────┤   to citizen automatically   │
  │                                 │                              │
  ├─ Checks /citizen/complaints     │                              │
  ├─ Visits /citizen/rewards        │                              │
  ├─ Redeems reward ───────────────►│                              │
  │                                 │◄────── Admin approves ───────┤
```

**Complaint status lifecycle:** `Submitted → Under Review → In Progress → Resolved`

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Python 3.10+, Flask 3 |
| Database | MySQL 8 |
| Auth | Werkzeug password hashing, Flask server-side sessions |
| File Storage | Local (`static/uploads/`) |

---

## Project Structure

```
smart-waste-management/
│
├── app.py                      ← Flask app — all 34 routes across three portals
├── config.py                   ← All configuration (reads .env)
├── create_admin.py             ← One-time CLI script to create admin accounts
├── requirements.txt
├── .env.example                ← Copy to .env and configure
├── .gitignore
├── README.md
├── TESTING.md                  ← 40+ manual test cases
├── VIVA.md                     ← 25 viva Q&A for project evaluation
│
├── database/
│   └── schema.sql              ← Creates all 7 tables (run once)
│
├── templates/
│   ├── landing.html            ← Portal selector — Citizen / Admin / Staff cards
│   ├── base.html               ← Public pages layout (navbar, flash, footer)
│   ├── index.html              ← Public homepage with live stats
│   ├── report.html             ← Anonymous complaint form (preserved)
│   ├── track.html              ← Public complaint tracker
│   ├── success.html            ← Submission confirmation
│   ├── about.html              ← Project info
│   │
│   ├── citizen/
│   │   ├── base.html           ← Citizen portal layout (green navbar)
│   │   ├── login.html          ← Email + password login
│   │   ├── register.html       ← Public registration form
│   │   ├── dashboard.html      ← Stats, Green Points, recent complaints
│   │   ├── report.html         ← Report waste (linked to citizen account)
│   │   ├── complaints.html     ← All my complaints table
│   │   ├── complaint_detail.html ← Status timeline + photos
│   │   ├── rewards.html        ← Green Points wallet + marketplace
│   │   └── profile.html        ← Edit name and phone
│   │
│   ├── admin/
│   │   ├── base.html           ← Admin portal layout (blue navbar)
│   │   ├── login.html          ← Username + password login
│   │   ├── dashboard.html      ← 7 stat cards + category chart + recent complaints
│   │   ├── complaints.html     ← Search/filter all complaints
│   │   ├── complaint_detail.html ← Full detail + status update + staff assignment
│   │   ├── staff_list.html     ← All staff members + open task counts
│   │   ├── staff_add.html      ← Create new staff account
│   │   └── rewards.html        ← Approve/reject redemptions + catalogue
│   │
│   ├── staff/
│   │   ├── base.html           ← Staff portal layout (orange navbar)
│   │   ├── login.html          ← Email + password login
│   │   ├── dashboard.html      ← Assigned tasks sorted by urgency
│   │   └── task_detail.html    ← Task info + status update + after-photo upload
│   │
│   └── errors/
│       ├── 404.html
│       └── 500.html
│
├── static/
│   ├── css/style.css           ← Full design system (all three portals)
│   ├── js/script.js            ← Mobile nav, flash dismiss, active links
│   └── uploads/                ← Complaint and after-cleaning images saved here
│
└── utils/
    ├── __init__.py
    └── helpers.py              ← DB conn, ID generators, file upload, Green Points, formatters
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- MySQL 8.0 or higher

### 1. Enter the project folder

```bash
cd smart-waste-management
```

### 2. Create a virtual environment

**macOS / Linux**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows**
```bat
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up MySQL

```bash
mysql -u root -p < database/schema.sql
```

This creates `smart_waste_db` and all 7 tables. You can also open the file in MySQL Workbench and run it there.

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```
SECRET_KEY=replace-with-a-long-random-string
DB_HOST=localhost
DB_PORT=3306
DB_NAME=smart_waste_db
DB_USER=root
DB_PASSWORD=your_mysql_password
```

### 6. Create the first admin account

```bash
python create_admin.py
```

Prompts for a username and password interactively. The password is hashed — never stored in plain text.

### 7. Start the server

```bash
python app.py
```

Open **http://127.0.0.1:5000** — the portal landing page appears.

---

## All Routes

### Public

| Method | URL | Description |
|---|---|---|
| GET | `/` | Landing page — portal selector |
| GET | `/report` | Anonymous complaint form |
| POST | `/report` | Submit anonymous complaint |
| GET | `/track?id=<id>` | Track any complaint by ID |
| GET | `/about` | About page |
| GET | `/db-test` | Dev only — MySQL connection check |

### Citizen Portal

| Method | URL | Auth | Description |
|---|---|---|---|
| GET/POST | `/citizen/register` | Public | Self-registration |
| GET/POST | `/citizen/login` | Public | Email + password login |
| GET | `/citizen/logout` | — | Clear session |
| GET | `/citizen/dashboard` | ✅ | Stats, Green Points, recent reports |
| GET/POST | `/citizen/report` | ✅ | Submit a complaint (linked to account) |
| GET | `/citizen/complaints` | ✅ | All my complaints |
| GET | `/citizen/complaint/<id>` | ✅ | Complaint detail (own only) |
| GET | `/citizen/rewards` | ✅ | Green Points wallet + marketplace |
| POST | `/citizen/rewards/redeem/<id>` | ✅ | Redeem a reward |
| GET/POST | `/citizen/profile` | ✅ | Edit profile |

### Admin Portal

| Method | URL | Auth | Description |
|---|---|---|---|
| GET/POST | `/admin/login` | Public | Username + password login |
| GET | `/admin/logout` | — | Clear session |
| GET | `/admin/dashboard` | ✅ | Stats, category chart, recent complaints |
| GET | `/admin/complaints` | ✅ | All complaints — search + filter |
| GET | `/admin/complaint/<id>` | ✅ | Complaint detail |
| POST | `/admin/complaint/<id>/update-status` | ✅ | Change complaint status |
| POST | `/admin/complaint/<id>/assign` | ✅ | Assign/unassign staff |
| GET | `/admin/staff` | ✅ | Staff list with open task counts |
| GET/POST | `/admin/staff/add` | ✅ | Create staff account |
| POST | `/admin/staff/<id>/toggle` | ✅ | Activate / deactivate staff |
| GET | `/admin/rewards` | ✅ | Pending redemptions + catalogue |
| POST | `/admin/rewards/redemption/<id>/approve` | ✅ | Approve redemption |
| POST | `/admin/rewards/redemption/<id>/reject` | ✅ | Reject + refund points |

### Staff Portal

| Method | URL | Auth | Description |
|---|---|---|---|
| GET/POST | `/staff/login` | Public | Email + password login |
| GET | `/staff/logout` | — | Clear session |
| GET | `/staff/dashboard` | ✅ | Assigned tasks sorted by urgency |
| GET | `/staff/task/<id>` | ✅ | Task detail (own tasks only) |
| POST | `/staff/task/<id>/update` | ✅ | Update status + upload after-photo |

---

## Database Schema

### `admins`
| Column | Type | Notes |
|---|---|---|
| id | INT AUTO_INCREMENT PK | |
| username | VARCHAR(80) | Unique |
| password_hash | VARCHAR(255) | Werkzeug pbkdf2:sha256 |
| created_at | DATETIME | |

### `citizens`
| Column | Type | Notes |
|---|---|---|
| id | INT AUTO_INCREMENT PK | |
| name | VARCHAR(120) | |
| email | VARCHAR(180) | Unique |
| phone | VARCHAR(20) | Nullable |
| password_hash | VARCHAR(255) | |
| green_points | INT | Default 0 |
| is_active | TINYINT(1) | |
| created_at / updated_at | DATETIME | |

### `staff`
| Column | Type | Notes |
|---|---|---|
| id | INT AUTO_INCREMENT PK | |
| name | VARCHAR(120) | |
| email | VARCHAR(180) | Unique |
| phone | VARCHAR(20) | Nullable |
| password_hash | VARCHAR(255) | |
| employee_id | VARCHAR(30) | Unique, e.g. `STAFF-A3F9K2` |
| zone | VARCHAR(100) | Nullable |
| is_active | TINYINT(1) | |
| created_by_admin | INT | FK → admins |
| created_at / updated_at | DATETIME | |

### `complaints`
| Column | Type | Notes |
|---|---|---|
| id | INT AUTO_INCREMENT PK | |
| complaint_id | VARCHAR(30) | Unique, e.g. `WMS-20241115-A3F9K2` |
| citizen_id | INT | FK → citizens, nullable (anonymous) |
| description | TEXT | |
| category | VARCHAR(50) | Plastic / Wet Waste / Dry Waste / Other |
| location | VARCHAR(255) | |
| image_path | VARCHAR(255) | Nullable |
| after_image_path | VARCHAR(255) | Nullable — uploaded by staff |
| status | ENUM | Submitted / Under Review / In Progress / Resolved |
| assigned_staff_id | INT | FK → staff, nullable |
| green_points_awarded | INT | Default 0 |
| created_at / updated_at | DATETIME | |

### `green_points_log`
Audit trail — one row per credit or debit. Linked to `citizens` and optionally `complaints`.

### `rewards`
Reward items in the marketplace. Seeded with 5 eco-friendly items on first schema run.

### `reward_redemptions`
Tracks citizen redemption requests. Status: `Pending → Approved / Rejected`.

---

## Security

| Concern | Implementation |
|---|---|
| Password storage | Werkzeug `generate_password_hash` — pbkdf2:sha256, never plain text |
| SQL injection | All queries use parameterized `%s` placeholders — no string concatenation |
| File upload safety | Extension whitelist (PNG/JPG/GIF/WEBP), UUID filename, `secure_filename()`, 5 MB limit |
| Role isolation | Three independent session keys: `citizen_id`, `admin_logged_in`, `staff_id` |
| Row-level access | Citizens query `WHERE citizen_id = session_id`; staff query `WHERE assigned_staff_id = session_id` |
| No role escalation | Citizen registration always sets `citizen` role; staff/admin accounts require admin action |
| Session fixation | `session.clear()` before writing any new session on login |
| XSS | Jinja2 auto-escapes all template variables by default |
| Open redirect | `next` parameter validated to only allow same-portal paths |
| Cookie security | `HttpOnly=True`, `SameSite=Lax`; `Secure` flag configurable via `.env` |
| Secrets | All sensitive values in `.env`, never in source code |

---

## Green Points System

Citizens earn **10 Green Points** automatically whenever a complaint they submitted is marked **Resolved** — either by an admin or by a staff member.

Points are deducted when a citizen redeems a reward. All transactions are recorded in `green_points_log`.

Redemptions start in `Pending` status and require admin approval. Rejecting a redemption refunds the points instantly.

---

## Future Enhancements

1. Interactive map (Leaflet.js) showing complaint locations and status
2. Email notifications when complaint status changes
3. Pagination on complaint tables
4. Admin notes/comments on individual complaints
5. Data export (CSV/PDF) from admin panel
6. AI-based waste photo classification to auto-suggest category
7. Heatmap of complaint hotspots by neighbourhood
8. SMS notifications via Twilio
9. Multiple admin roles (super-admin, viewer)
10. Mobile app (React Native or Flutter)
11. Automatic garbage collection route optimisation
12. Municipal API integration for official dispatch

---

## Development Notes

- Run with `python app.py` — Flask development server on `http://127.0.0.1:5000`
- The `/db-test` route confirms MySQL connectivity — remove before any public deployment
- Uploaded images go to `static/uploads/` and are served by Flask's static file handler
- After-cleaning photos are stored in `static/uploads/after/`
- `create_admin.py` can be run multiple times to add more admin accounts
