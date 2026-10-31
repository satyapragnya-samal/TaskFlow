# TaskFlow — Collaborative Task and Project Management Tool

TaskFlow is a role-based project and task management web application developed as a 5th-Semester Software Engineering project. It provides an intuitive workspace for software teams to manage project deliverables, assign tasks to members, track deadlines, visualize workflows on an interactive Kanban board, and monitor project performance with Chart.js analytics.

---

## 1. Technology Stack

- **Backend Framework:** Python Flask 3.0
- **Database Engine:** MySQL 8.0 (InnoDB)
- **Database ORM:** Flask-SQLAlchemy
- **Authentication & Sessions:** Flask-Login & Werkzeug Security (scrypt/pbkdf2 hashing)
- **Forms & CSRF Defense:** Flask-WTF & WTForms
- **Frontend & UI:** Bootstrap 5, Bootstrap Icons, Custom CSS
- **Visual Analytics:** Chart.js 4.4
- **Automated Testing:** Pytest

---

## 2. Relational Database Design (3NF)

The database schema adheres to Third Normal Form (3NF) to eliminate data redundancy and preserve referential integrity:

1. **`users`**: Manages credentials, roles (`admin` vs `user`), and activation state.
2. **`projects`**: Project metadata, start dates, target deadlines, and ownership ties.
3. **`project_members`**: Join table binding users to projects with contextual roles (`owner` vs `member`) and a `UNIQUE(project_id, user_id)` constraint.
4. **`tasks`**: Task records with priority, status (`todo`, `in_progress`, `in_review`, `completed`), assignees, and target completion dates.
5. **`task_comments`**: Threaded discussion entries tied to specific tasks.
6. **`notifications`**: Targeted user alerts for assignments and status updates.
7. **`activity_logs`**: System audit trail tracking all structural mutations across projects.

---

## 3. Project Structure

```text
taskflow/
├── routes/
│   ├── __init__.py           # Package marker
│   ├── auth.py               # Authentication blueprint (/auth)
│   ├── auth_forms.py         # Login, registration, profile WTForms
│   ├── dashboard.py          # Dashboard KPIs & Chart.js aggregates (/dashboard)
│   ├── projects.py           # Project CRUD & team membership (/projects)
│   ├── project_forms.py      # Project creation and team invite WTForms
│   ├── tasks.py              # Task CRUD, search filters & Kanban updates (/tasks)
│   ├── task_forms.py         # Task creation, editing & comment WTForms
│   ├── notifications.py      # In-app notifications & read receipts (/notifications)
│   └── admin.py              # System administration & user ledger (/admin)
├── static/
│   ├── css/style.css         # Custom UI variables & Kanban column layout
│   └── js/kanban.js          # HTML5 drag-and-drop controller with AJAX Fetch
├── templates/
│   ├── base.html             # UI shell, navbar, alerts & unread badge hook
│   ├── auth/                 # Login, register, profile templates
│   ├── dashboard/            # KPI cards & Chart.js canvas views
│   ├── projects/             # Project cards, creation form & workspace details
│   ├── tasks/                # Form, detail & Kanban board templates
│   ├── notifications/        # User notification center
│   ├── admin/                # Global account administration
│   └── errors/               # Custom HTTP error pages (403, 404, 500)
├── utils/
│   ├── __init__.py           # Package marker
│   ├── decorators.py         # Custom @admin_required route guard
│   └── notifications.py      # Automated notification dispatcher helper
├── tests/
│   ├── conftest.py           # Pytest test client and in-memory DB fixtures
│   ├── test_auth.py          # Authentication & hashing unit tests
│   └── test_projects_tasks.py# RBAC & Kanban API unit tests
├── .env.example              # Environment variables template
├── .gitignore                # Excludes secrets, venv, and cache
├── app.py                    # Application factory (create_app) & runner
├── config.py                 # Centralized configuration loader
├── extensions.py             # Decoupled instances of db, login_manager, csrf
├── models.py                 # SQLAlchemy relational schema
├── requirements.txt          # Dependency lockfile
└── README.md                 # Project documentation