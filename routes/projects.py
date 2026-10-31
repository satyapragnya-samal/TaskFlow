from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import Project, ProjectMember, User, ActivityLog
from routes.project_forms import ProjectForm, AddMemberForm

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

@projects_bp.route('/')
@login_required
def index():
    # Fetch all projects where the user is an owner or a registered member
    member_project_ids = db.session.query(ProjectMember.project_id).filter_by(user_id=current_user.id).subquery()
    user_projects = Project.query.filter(
        (Project.owner_id == current_user.id) | (Project.id.in_(member_project_ids))
    ).order_by(Project.created_at.desc()).all()

    return render_template('projects/index.html', projects=user_projects)


@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            title=form.title.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            priority=form.priority.data,
            start_date=form.start_date.data,
            deadline=form.deadline.data,
            owner_id=current_user.id
        )
        db.session.add(project)
        db.session.flush()  # Populates project.id before commit

        # Automatically enroll creator as project owner in project_members
        membership = ProjectMember(
            project_id=project.id,
            user_id=current_user.id,
            role='owner'
        )
        db.session.add(membership)

        # Log project creation activity
        log = ActivityLog(
            project_id=project.id,
            user_id=current_user.id,
            action="PROJECT_CREATED",
            details=f"Project '{project.title}' was created."
        )
        db.session.add(log)
        db.session.commit()

        flash(f"Project '{project.title}' created successfully!", 'success')
        return redirect(url_for('projects.detail', project_id=project.id))

    return render_template('projects/create.html', form=form, title="Create New Project")


@projects_bp.route('/<int:project_id>')
@login_required
def detail(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Access control: Verify user is owner or enrolled member
    membership = ProjectMember.query.filter_by(project_id=project.id, user_id=current_user.id).first()
    if project.owner_id != current_user.id and not membership and current_user.role != 'admin':
        abort(403)

    is_owner = (project.owner_id == current_user.id or current_user.role == 'admin')
    member_form = AddMemberForm()

    # Calculate basic task metrics for this project
    total_tasks = len(project.tasks)
    completed_tasks = len([t for t in project.tasks if t.status == 'completed'])
    progress_percentage = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    return render_template(
        'projects/detail.html',
        project=project,
        is_owner=is_owner,
        member_form=member_form,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        progress_percentage=progress_percentage
    )


@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)

    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        project.title = form.title.data.strip()
        project.description = form.description.data.strip() if form.description.data else None
        project.priority = form.priority.data
        project.start_date = form.start_date.data
        project.deadline = form.deadline.data

        db.session.commit()
        flash('Project updated successfully.', 'success')
        return redirect(url_for('projects.detail', project_id=project.id))

    return render_template('projects/create.html', form=form, title=f"Edit Project: {project.title}")


@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete(project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)

    title = project.title
    db.session.delete(project)
    db.session.commit()

    flash(f"Project '{title}' has been deleted.", 'info')
    return redirect(url_for('projects.index'))


@projects_bp.route('/<int:project_id>/members/add', methods=['POST'])
@login_required
def add_member(project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)

    form = AddMemberForm()
    if form.validate_on_submit():
        target_ident = form.username_or_email.data.strip()
        user = User.query.filter(
            (User.username == target_ident) | (User.email == target_ident.lower())
        ).first()

        if not user:
            flash(f"No user found matching '{target_ident}'.", 'danger')
            return redirect(url_for('projects.detail', project_id=project.id))

        existing_member = ProjectMember.query.filter_by(project_id=project.id, user_id=user.id).first()
        if existing_member:
            flash(f"'{user.full_name}' is already a member of this project.", 'warning')
            return redirect(url_for('projects.detail', project_id=project.id))

        new_member = ProjectMember(project_id=project.id, user_id=user.id, role='member')
        db.session.add(new_member)

        # Log activity
        log = ActivityLog(
            project_id=project.id,
            user_id=current_user.id,
            action="MEMBER_ADDED",
            details=f"Added '{user.full_name}' to the project team."
        )
        db.session.add(log)
        db.session.commit()

        flash(f"Added '{user.full_name}' to project team.", 'success')

    return redirect(url_for('projects.detail', project_id=project.id))


@projects_bp.route('/<int:project_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_member(project_id, user_id):
    project = Project.query.get_or_404(project_id)
    if project.owner_id != current_user.id and current_user.role != 'admin':
        abort(403)

    if user_id == project.owner_id:
        flash("The project owner cannot be removed from the project.", 'danger')
        return redirect(url_for('projects.detail', project_id=project.id))

    membership = ProjectMember.query.filter_by(project_id=project.id, user_id=user_id).first_or_404()
    removed_user_name = membership.user.full_name
    db.session.delete(membership)

    log = ActivityLog(
        project_id=project.id,
        user_id=current_user.id,
        action="MEMBER_REMOVED",
        details=f"Removed '{removed_user_name}' from the project."
    )
    db.session.add(log)
    db.session.commit()

    flash(f"Removed '{removed_user_name}' from the team.", 'info')
    return redirect(url_for('projects.detail', project_id=project.id))