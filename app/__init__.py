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
    upload_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
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
        # Create default owner account if not exists
        from .models.user import User
        from .utils.constants import UserRole
        owner = User.query.filter_by(role=UserRole.OWNER).first()
        if not owner:
            owner = User(
                username='owner',
                email='owner@charity.org',
                full_name='System Owner',
                phone='0000000000',
                role=UserRole.OWNER
            )
            owner.set_password('owner123')
            db.session.add(owner)
            db.session.commit()

    return app
