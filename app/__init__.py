from functools import wraps
from flask import Flask, flash, redirect, url_for
from flask_login import LoginManager, current_user
from flask_pymongo import PyMongo
from app.models.models import users, User
from flask_login import LoginManager
from flask_pymongo import PyMongo


mongo = PyMongo()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    user = mongo.db.users.find_one({"username": user_id})
    if user:
        return User(id=user['username'], name=user['name'], role=user['role']) 
    return None

def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Kiểm tra người dùng đã đăng nhập chưa
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            # Kiểm tra vai trò của người dùng
            if current_user.role not in roles:  # Thay đổi ở đây
                flash("Bạn không có quyền truy cập vào trang này.")
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper
   
    
def create_app():
    app = Flask(__name__)
    # app.config["MONGO_URI"] = "mongodb://localhost:27017/thuctap"
    app.config["MONGO_URI"] = "mongodb+srv://dduoc2002:1kNlNH22DZLjssr9@data-alyst.uowmx.mongodb.net/webdata?retryWrites=true&w=majority"
    app.secret_key = 'Hello9876541312'

    mongo.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'


    from app.controllers.main import main_bp
    from app.controllers.auth import auth_bp 
    from app.controllers.admin import admin_bp 
    from app.controllers.view import view_bp 
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(view_bp, url_prefix='/History')


    return app