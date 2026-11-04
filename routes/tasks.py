from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from extensions import db
from models import Project, ProjectMember, Task, TaskComment, ActivityLog
from routes.task_forms import TaskForm, CommentForm
from utils.notifications import send_notification

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')


def get_project_and_verify_access(project_id):
    """Verifies that the project exists and current_user has access permissions."""
    project = Project.query.get_or_404(project_id)
    membership = ProjectMember.query.filter_by(project_id=project.id, user_id=current_user.id).first()
    
    # Allow access if user is owner, project member, or system administrator
    if project.owner_id != current_user.id and not membership and current_user.role != 'admin':
        abort(403)
        
    is_owner = (project.owner_id == current_user.id or current_user.role == 'admin')
    return project, is_owner


@tasks_bp.route('/project/<int:project_id>/create', methods=['GET', 'POST'])
@login_required
def create(project_id):
    """Creates a new task tied to the specified project."""
    project, is_owner = get_project_and_verify_access(project_id)

    form = TaskForm()
    
    # Populate assignee dropdown safely with project members
    choices = [(0, 'Unassigned')]
    for m in project.members:
        if m.user:
            choices.append((m.user.id, f"{m.user.full_name} (@{m.user.username})"))
    form.assignee_id.choices = choices

    if form.validate_on_submit():
        assignee_val = form.assignee_id.data
        assignee_id = assignee_val if (assignee_val and assignee_val != 0) else None

        task = Task(
            project_id=project.id,
            title=form.title.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            priority=form.priority.data,
            status=form.status.data,
            creator_id=current_user.id,
            assignee_id=assignee_id,
            due_date=form.due_date.data
        )
        if task.status == 'completed':
            task.completed_at = datetime.utcnow()

        db.session.add(task)
        db.session.flush()

        # Audit log creation
        log = ActivityLog(
            project_id=project.id,
            user_id=current_user.id,
            action="TASK_CREATED",
            details=f"Created task '{task.title}'."
        )
        db.session.add(log)
        db.session.commit()

        # Trigger notification if assigned to another user
        if task.assignee_id and task.assignee_id != current_user.id:
            send_notification(
                user_id=task.assignee_id,
                title="New Task Assigned",
                message=f"You have been assigned to '{task.title}' in project '{project.title}'.",
                link=url_for('tasks.detail', task_id=task.id)
            )

        flash(f"Task '{task.title}' created successfully.", 'success')
        return redirect(url_for('tasks.kanban', project_id=project.id))

    return render_template('tasks/form.html', form=form, project=project, title="Create Task")


@tasks_bp.route('/project/<int:project_id>/list')
@login_required
def list_tasks(project_id):
    """Filterable task list with MySQL-safe ordering."""
    project, is_owner = get_project_and_verify_access(project_id)
    query = Task.query.filter_by(project_id=project.id)

    # Keyword search across title and description
    search_query = request.args.get('q', '').strip()
    if search_query:
        query = query.filter(
            or_(
                Task.title.ilike(f'%{search_query}%'),
                Task.description.ilike(f'%{search_query}%')
            )
        )

    # Status filter
    status_filter = request.args.get('status', '').strip()
    if status_filter:
        query = query.filter(Task.status == status_filter)

    # Priority filter
    priority_filter = request.args.get('priority', '').strip()
    if priority_filter:
        query = query.filter(Task.priority == priority_filter)

    # Assignee filter
    assignee_filter = request.args.get('assignee', type=int)
    if assignee_filter:
        query = query.filter(Task.assignee_id == assignee_filter)

    # Sorting logic compatible with MySQL engines
    sort_by = request.args.get('sort', 'due_date')
    if sort_by == 'due_date':
        query = query.order_by(Task.due_date.asc())
    elif sort_by == 'created':
        query = query.order_by(Task.created_at.desc())
    elif sort_by == 'priority':
        query = query.order_by(Task.priority.desc())

    tasks = query.all()

    return render_template(
        'tasks/list.html',
        project=project,
        tasks=tasks,
        is_owner=is_owner,
        search_query=search_query,
        status_filter=status_filter,
        priority_filter=priority_filter,
        assignee_filter=assignee_filter,
        sort_by=sort_by
    )


@tasks_bp.route('/<int:task_id>')
@login_required
def detail(task_id):
    """Detailed view for a specific task and its comment feed."""
    task = Task.query.get_or_404(task_id)
    project, is_owner = get_project_and_verify_access(task.project_id)
    form = CommentForm()

    return render_template(
        'tasks/detail.html',
        task=task,
        project=project,
        is_owner=is_owner,
        comment_form=form
    )


@tasks_bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    """Edits an existing task."""
    task = Task.query.get_or_404(task_id)
    project, is_owner = get_project_and_verify_access(task.project_id)

    can_edit = is_owner or task.creator_id == current_user.id or task.assignee_id == current_user.id
    if not can_edit:
        abort(403)

    form = TaskForm(obj=task)
    choices = [(0, 'Unassigned')]
    for m in project.members:
        if m.user:
            choices.append((m.user.id, f"{m.user.full_name} (@{m.user.username})"))
    form.assignee_id.choices = choices

    if request.method == 'GET':
        form.assignee_id.data = task.assignee_id or 0

    if form.validate_on_submit():
        previous_status = task.status
        old_assignee = task.assignee_id

        task.title = form.title.data.strip()
        task.description = form.description.data.strip() if form.description.data else None
        task.priority = form.priority.data
        task.status = form.status.data
        assignee_val = form.assignee_id.data
        task.assignee_id = assignee_val if (assignee_val and assignee_val != 0) else None
        task.due_date = form.due_date.data

        if task.status == 'completed' and previous_status != 'completed':
            task.completed_at = datetime.utcnow()
        elif task.status != 'completed':
            task.completed_at = None

        log = ActivityLog(
            project_id=project.id,
            user_id=current_user.id,
            action="TASK_UPDATED",
            details=f"Updated task '{task.title}'."
        )
        db.session.add(log)
        db.session.commit()

        if task.assignee_id and task.assignee_id != old_assignee and task.assignee_id != current_user.id:
            send_notification(
                user_id=task.assignee_id,
                title="Task Assignment Changed",
                message=f"You are now assigned to '{task.title}' in '{project.title}'.",
                link=url_for('tasks.detail', task_id=task.id)
            )

        flash("Task updated successfully.", 'success')
        return redirect(url_for('tasks.detail', task_id=task.id))

    return render_template('tasks/form.html', form=form, project=project, title=f"Edit: {task.title}")


@tasks_bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def delete(task_id):
    """Deletes a task record."""
    task = Task.query.get_or_404(task_id)
    project, is_owner = get_project_and_verify_access(task.project_id)

    if not is_owner and task.creator_id != current_user.id:
        abort(403)

    project_id = task.project_id
    title = task.title

    db.session.delete(task)
    log = ActivityLog(
        project_id=project_id,
        user_id=current_user.id,
        action="TASK_DELETED",
        details=f"Deleted task '{title}'."
    )
    db.session.add(log)
    db.session.commit()

    flash(f"Task '{title}' has been deleted.", 'info')
    return redirect(url_for('tasks.kanban', project_id=project_id))


@tasks_bp.route('/project/<int:project_id>/kanban')
@login_required
def kanban(project_id):
    """Renders the 4-column visual Kanban board."""
    project, is_owner = get_project_and_verify_access(project_id)

    tasks_by_column = {
        'todo': [t for t in project.tasks if t.status == 'todo'],
        'in_progress': [t for t in project.tasks if t.status == 'in_progress'],
        'in_review': [t for t in project.tasks if t.status == 'in_review'],
        'completed': [t for t in project.tasks if t.status == 'completed'],
    }

    return render_template(
        'tasks/kanban.html',
        project=project,
        is_owner=is_owner,
        columns=tasks_by_column
    )


@tasks_bp.route('/<int:task_id>/update-status', methods=['POST'])
@login_required
def update_status_ajax(task_id):
    """Asynchronously updates task status on Kanban drag-and-drop actions."""
    task = Task.query.get_or_404(task_id)
    project, is_owner = get_project_and_verify_access(task.project_id)

    data = request.get_json() or {}
    new_status = data.get('status')
    valid_statuses = ['todo', 'in_progress', 'in_review', 'completed']

    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400

    old_status = task.status
    task.status = new_status
    if new_status == 'completed':
        task.completed_at = datetime.utcnow()
    else:
        task.completed_at = None

    log = ActivityLog(
        project_id=project.id,
        user_id=current_user.id,
        action="STATUS_CHANGED",
        details=f"Moved '{task.title}' from {old_status} to {new_status}."
    )
    db.session.add(log)
    db.session.commit()

    if new_status == 'completed' and project.owner_id != current_user.id:
        send_notification(
            user_id=project.owner_id,
            title="Task Completed",
            message=f"'{current_user.full_name}' completed the task '{task.title}'.",
            link=url_for('tasks.detail', task_id=task.id)
        )

    return jsonify({'success': True, 'task_id': task.id, 'new_status': new_status})


@tasks_bp.route('/<int:task_id>/comments', methods=['POST'])
@login_required
def add_comment(task_id):
    """Adds a discussion comment to a task."""
    task = Task.query.get_or_404(task_id)
    get_project_and_verify_access(task.project_id)

    form = CommentForm()
    if form.validate_on_submit():
        comment = TaskComment(
            task_id=task.id,
            user_id=current_user.id,
            content=form.content.data.strip()
        )
        db.session.add(comment)
        db.session.commit()

        if task.assignee_id and task.assignee_id != current_user.id:
            send_notification(
                user_id=task.assignee_id,
                title="New Comment on Task",
                message=f"{current_user.full_name} commented on '{task.title}'.",
                link=url_for('tasks.detail', task_id=task.id)
            )

        flash('Comment posted.', 'success')

    return redirect(url_for('tasks.detail', task_id=task.id))