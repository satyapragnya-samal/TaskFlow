from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Project, Task, TaskComment
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    
    # Global system statistics
    stats = {
        'total_users': User.query.count(),
        'total_projects': Project.query.count(),
        'total_tasks': Task.query.count(),
        'total_comments': TaskComment.query.count()
    }
    
    return render_template('admin/users.html', users=all_users, stats=stats)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_status(user_id):
    if user_id == current_user.id:
        flash("You cannot deactivate your own administrative account.", "danger")
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)
    user.is_active_account = not user.is_active_account
    db.session.commit()

    status_str = "activated" if user.is_active_account else "deactivated"
    flash(f"Account for '{user.username}' has been {status_str}.", "info")
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/toggle-role', methods=['POST'])
@login_required
@admin_required
def toggle_role(user_id):
    if user_id == current_user.id:
        flash("You cannot revoke your own administrator role.", "danger")
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)
    user.role = 'user' if user.role == 'admin' else 'admin'
    db.session.commit()

    flash(f"Role for '{user.username}' updated to '{user.role.upper()}'.", "success")
    return redirect(url_for('admin.users'))