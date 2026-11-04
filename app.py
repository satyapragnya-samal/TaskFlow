from flask import Flask, redirect, url_for, render_template
from flask_login import current_user
from config import Config
from extensions import db, login_manager, csrf

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.projects import projects_bp
    from routes.tasks import tasks_bp
    from routes.dashboard import dashboard_bp
    from routes.notifications import notifications_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Global error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    # Global context processor: Injects unread notification count
    @app.context_processor
    def inject_notification_count():
        if current_user.is_authenticated:
            from models import Notification
            count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            return {'unread_notif_count': count}
        return {'unread_notif_count': 0}

    # Root route redirects to dashboard
    @app.route('/')
    def index():
        return redirect(url_for('dashboard.index'))

    @app.route('/health')
    def health():
        return {'status': 'healthy', 'app': 'TaskFlow'}, 200

    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        import models
        db.create_all()
        print("Database tables verified and initialized successfully in MySQL.")

    # use_reloader=False stops the silent Python 3.13 crash on Windows
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)