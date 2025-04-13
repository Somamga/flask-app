from flask import Flask, session
import os

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def create_app():
    # ✅ ここが重要！
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    app.secret_key = 'super-secret-key'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

    from .auth import auth_bp
    from .views import views_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)

    @app.context_processor
    def inject_user():
        return dict(logged_in_user=session.get('username'))

    return app
