from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.models import User
from app import mongo

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash("Bạn đã đăng nhập!")
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Lấy thông tin người dùng từ MongoDB
        user = mongo.db.users.find_one({"username": username})

        if user and user['password'] == password:
            user_obj = User(id=user['username'], name=user['name'], role=user['role'])
            login_user(user_obj)
            flash("Đăng nhập thành công!")
            return redirect(url_for('main.dashboard'))
        else:
            flash("Tên đăng nhập hoặc mật khẩu không chính xác")
    
    return render_template('login.html')

@auth_bp.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    flash("Bạn đã đăng xuất!")
    return redirect(url_for('auth.login'))
