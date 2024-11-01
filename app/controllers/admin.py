from bson import ObjectId
from flask import Blueprint, flash, request, render_template, redirect, url_for, send_file
from flask_login import login_required, current_user
import pandas as pd
from datetime import datetime
from app.models.models import User
from werkzeug.security import generate_password_hash
from app import mongo, role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manage') 
def manage():
    users = mongo.db.users.find()  
    
    return render_template('manage.html', users=users)

@admin_bp.route('/create-account', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manage') 
def create_account():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')  # Bảo mật password!

        # Kiểm tra thông tin và thêm vào MongoDB
        mongo.db.users.insert_one({
            'username': username,
            'email': email,
            'role': role,
            'name': name,  
            'password': password,   #generate_password_hash(password),  # Hash mật khẩu
            'time_created': datetime.now()
        })
        flash('Tài khoản đã được thêm thành công!', 'success')
        return redirect(url_for('admin.manage'))

    return render_template('manage-add.html')

@admin_bp.route('/delete/<user_id>', methods=['POST'])
@login_required
@role_required('admin', 'manage') 
def delete(user_id):
    # Xóa người dùng khỏi collection `user`
    mongo.db.users.delete_one({'_id': ObjectId(user_id)})
    flash('Người dùng đã được xóa thành công!', 'success')
    return redirect(url_for('admin.manage'))


from werkzeug.security import generate_password_hash

@admin_bp.route('/update-account/<user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manage') 
def update_account(user_id):
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        flash('Người dùng không tồn tại!', 'danger')
        return redirect(url_for('admin.manage'))

    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')  
        role = request.form.get('role')
        new_password = request.form.get('password')
        
        update_data = {
            'name': name,  
            'email': email,
            'role': role
        }
        # Kiểm tra và cập nhật mật khẩu nếu có
        if new_password:
            update_data['password'] = generate_password_hash(new_password)

        result = mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            flash('Cập nhật tài khoản thành công!', 'success')
        else:
            flash('Không có thay đổi nào được thực hiện!', 'warning')

        return redirect(url_for('admin.manage'))

    return render_template('manage-update.html', user=user)
