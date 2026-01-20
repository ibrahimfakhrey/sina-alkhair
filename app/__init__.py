from flask import Flask
from .config import Config
from .extensions import db, jwt, cors
import os


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Ensure upload folders exist
    upload_base = app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads'))
    for folder in ['screenshots', 'investigations', 'payment_proofs']:
        os.makedirs(os.path.join(upload_base, folder), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from .routes import auth, users, cases, research, approvals, finance, images, notifications, dashboard

    app.register_blueprint(auth.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(cases.bp)
    app.register_blueprint(research.bp)
    app.register_blueprint(approvals.bp)
    app.register_blueprint(finance.bp)
    app.register_blueprint(images.bp)
    app.register_blueprint(notifications.bp)
    app.register_blueprint(dashboard.bp)

    # Register error handlers
    from .middleware.error_handlers import register_error_handlers
    register_error_handlers(app)

    # Create database tables
    with app.app_context():
        db.create_all()
        # Create default accounts if not exists
        from .models.user import User
        from .utils.constants import UserRole

        # Default accounts to create
        default_accounts = [
            {'username': 'owner', 'email': 'owner@charity.org', 'full_name': 'System Owner', 'phone': '0000000000', 'role': UserRole.OWNER, 'password': 'owner123'},
            {'username': 'manager1', 'email': 'manager1@charity.org', 'full_name': 'Manager Cases', 'phone': '0000000001', 'role': UserRole.MANAGER_1, 'password': 'manager123'},
            {'username': 'manager2', 'email': 'manager2@charity.org', 'full_name': 'Manager Approvals', 'phone': '0000000002', 'role': UserRole.MANAGER_2, 'password': 'manager123'},
            {'username': 'manager3', 'email': 'manager3@charity.org', 'full_name': 'Manager Finance', 'phone': '0000000003', 'role': UserRole.MANAGER_3, 'password': 'manager123'},
            {'username': 'manager4', 'email': 'manager4@charity.org', 'full_name': 'Manager Reports', 'phone': '0000000004', 'role': UserRole.MANAGER_4, 'password': 'manager123'},
            {'username': 'manager5', 'email': 'manager5@charity.org', 'full_name': 'Manager Admin', 'phone': '0000000005', 'role': UserRole.MANAGER_5, 'password': 'manager123'},
            {'username': 'researcher1', 'email': 'researcher1@charity.org', 'full_name': 'Researcher One', 'phone': '0000000006', 'role': UserRole.RESEARCHER, 'password': 'researcher123'},
        ]

        for account in default_accounts:
            existing = User.query.filter_by(username=account['username']).first()
            if not existing:
                user = User(
                    username=account['username'],
                    email=account['email'],
                    full_name=account['full_name'],
                    phone=account['phone'],
                    role=account['role']
                )
                user.set_password(account['password'])
                db.session.add(user)

        db.session.commit()

    return app
