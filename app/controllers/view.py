from io import BytesIO
from flask import Blueprint, flash, request, render_template, redirect, url_for, send_file
from flask_login import login_required, current_user
import pandas as pd
from datetime import datetime
from app.models.models import User
from app.controllers.utils import calculate_percentile, calculate_point_value, duplicate_keywords, ensure_string_keys, search_keyword, three_nearest_months
from app import mongo

view_bp = Blueprint('view', __name__)


@view_bp.route('/', methods=['GET'])
@login_required
def history():
    collections = mongo.db.list_collection_names()
    
    user_collections = [collection for collection in collections if collection.startswith(str(current_user.id) + "_")]

    # Định dạng thời gian cho mỗi collection
    formatted_collections = []
    for collection in user_collections:
        # Lấy dữ liệu từ collection
        data = mongo.db[collection].find_one()
        
        # Bỏ qua nếu không có dữ liệu
        if data:
            # Lấy chuỗi thời gian sau dấu gạch dưới
            date_str = collection.split('_', 1)[1]  # Bỏ phần đầu tiên để lấy chuỗi thời gian
            date = date_str[:8]
            time = date_str[9:]

            # Định dạng ngày và giờ
            formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"  
            formatted_time = f"{time[:2]}:{time[2:4]}:{time[4:6]}" 

            # Thêm vào danh sách với định dạng
            formatted_collections.append({
                'name': collection,
                'date': formatted_date,
                'time': formatted_time,
                'original_filename': data.get('original_filename') ,
                'datetime': f"{date_str}"
            })
    formatted_collections.sort(key=lambda x: x['datetime'], reverse=True)

    return render_template('view-all.html', collections=formatted_collections)



@view_bp.route('/delete_collection/<collection>', methods=['POST'])
@login_required
def delete_data(collection):
    mongo.db.drop_collection(collection)
    return redirect(url_for('main.all_data'))

