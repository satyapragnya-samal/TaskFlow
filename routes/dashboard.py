from datetime import date
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import or_
from extensions import db
from models import Project, ProjectMember, Task, ActivityLog

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    # 1. Fetch all projects where the user is an owner or a registered member
    member_project_ids = db.session.query(ProjectMember.project_id).filter_by(user_id=current_user.id).subquery()
    user_projects = Project.query.filter(
        or_(Project.owner_id == current_user.id, Project.id.in_(member_project_ids))
    ).all()
    project_ids = [p.id for p in user_projects]

    total_projects = len(user_projects)

    # 2. Fetch all tasks belonging to accessible projects
    tasks = Task.query.filter(Task.project_id.in_(project_ids)).all() if project_ids else []

    total_tasks = len(tasks)
    todo_count = len([t for t in tasks if t.status == 'todo'])
    in_progress_count = len([t for t in tasks if t.status == 'in_progress'])
    in_review_count = len([t for t in tasks if t.status == 'in_review'])
    completed_count = len([t for t in tasks if t.status == 'completed'])

    today = date.today()
    overdue_count = len([t for t in tasks if t.due_date and t.due_date < today and t.status != 'completed'])

    completion_percentage = int((completed_count / total_tasks * 100)) if total_tasks > 0 else 0

    # 3. Tasks assigned directly to current logged-in user
    my_tasks = [t for t in tasks if t.assignee_id == current_user.id and t.status != 'completed']

    # 4. Upcoming deadlines (next 5 uncompleted tasks ordered by due date)
    upcoming_tasks = (
        Task.query.filter(
            Task.project_id.in_(project_ids),
            Task.status != 'completed',
            Task.due_date.isnot(None)
        )
        .order_by(Task.due_date.asc())
        .limit(5)
        .all()
        if project_ids else []
    )

    # 5. Recent audit activity logs across these projects
    recent_activities = (
        ActivityLog.query.filter(ActivityLog.project_id.in_(project_ids))
        .order_by(ActivityLog.created_at.desc())
        .limit(8)
        .all()
        if project_ids else []
    )

    # Status distribution for Chart.js
    chart_status_data = [todo_count, in_progress_count, in_review_count, completed_count]

    # Priority distribution for Chart.js
    low_count = len([t for t in tasks if t.priority == 'low'])
    med_count = len([t for t in tasks if t.priority == 'medium'])
    high_count = len([t for t in tasks if t.priority == 'high'])
    urgent_count = len([t for t in tasks if t.priority == 'urgent'])
    chart_priority_data = [low_count, med_count, high_count, urgent_count]

    return render_template(
        'dashboard/index.html',
        total_projects=total_projects,
        total_tasks=total_tasks,
        in_progress_count=in_progress_count,
        completed_count=completed_count,
        overdue_count=overdue_count,
        completion_percentage=completion_percentage,
        my_tasks=my_tasks,
        upcoming_tasks=upcoming_tasks,
        recent_activities=recent_activities,
        chart_status_data=chart_status_data,
        chart_priority_data=chart_priority_data
    )