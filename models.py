from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    """Callback required by Flask-Login to reload user object from session ID."""
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'admin' or 'user'
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    owned_projects = db.relationship('Project', backref='owner', cascade='all, delete-orphan', lazy=True)
    memberships = db.relationship('ProjectMember', backref='user', cascade='all, delete-orphan', lazy=True)
    assigned_tasks = db.relationship('Task', backref='assignee', foreign_keys='Task.assignee_id', lazy=True)
    created_tasks = db.relationship('Task', backref='creator', foreign_keys='Task.creator_id', lazy=True)
    comments = db.relationship('TaskComment', backref='author', cascade='all, delete-orphan', lazy=True)
    notifications = db.relationship('Notification', backref='recipient', cascade='all, delete-orphan', lazy=True)

    def set_password(self, password):
        """Hashes password using scrypt/pbkdf2 via Werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies candidate password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'completed', 'archived'
    priority = db.Column(db.String(20), default='medium', nullable=False)  # 'low', 'medium', 'high', 'urgent'
    start_date = db.Column(db.Date, nullable=True)
    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members = db.relationship('ProjectMember', backref='project', cascade='all, delete-orphan', lazy=True)
    tasks = db.relationship('Task', backref='project', cascade='all, delete-orphan', lazy=True)
    activities = db.relationship('ActivityLog', backref='project', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<Project {self.title}>'


class ProjectMember(db.Model):
    __tablename__ = 'project_members'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), default='member', nullable=False)  # 'owner', 'member'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='uq_project_user'),
    )

    def __repr__(self):
        return f'<ProjectMember User:{self.user_id} Project:{self.project_id}>'


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='todo', nullable=False)  # 'todo', 'in_progress', 'in_review', 'completed'
    priority = db.Column(db.String(20), default='medium', nullable=False)  # 'low', 'medium', 'high', 'urgent'
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    comments = db.relationship('TaskComment', backref='task', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<Task {self.title}>'


class TaskComment(db.Model):
    __tablename__ = 'task_comments'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<TaskComment id={self.id} task_id={self.task_id}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification id={self.id} user_id={self.user_id}>'


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # e.g., 'CREATED_TASK', 'STATUS_CHANGED'
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='activity_logs', lazy=True)

    def __repr__(self):
        return f'<ActivityLog id={self.id} action={self.action}>'
    