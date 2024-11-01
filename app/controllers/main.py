from io import BytesIO
from flask import Blueprint, flash, request, render_template, redirect, url_for, send_file
from flask_login import login_required, current_user
import pandas as pd
from datetime import datetime
from app.models.models import User
from app.controllers.utils import calculate_percentile, calculate_point_value, duplicate_keywords, ensure_string_keys, search_keyword, three_nearest_months
from app import mongo

main_bp = Blueprint('main', __name__)

@main_bp.route('/dashboard')
@login_required  
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/calculate_result', methods=['GET', 'POST'])
@login_required 
def calculate_result():
    from app import mongo 
    message=None
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        if file:
            data = pd.read_excel(file)
            
            data['Search Volume Percentile'] = calculate_percentile(data, 'Search Volume (Global)')
            data['CPC Percentile'] = calculate_percentile(data, 'CPC (Global)')
            data['Competition Percentile'] = calculate_percentile(data, 'Competition (Global)')

            final_data = calculate_point_value(data)
            final_data = final_data.drop(columns=['Search Volume Percentile', 'CPC Percentile', 'Competition Percentile'])          
            final_data = duplicate_keywords(final_data)
            records = final_data.to_dict(orient='records')
            records = [ensure_string_keys(record) for record in records]
            
            original_filename = file.filename
            collection_name = f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            for record in records:
                record['original_filename'] = original_filename
            
            mongo.db[collection_name].insert_many(records)

            return redirect(url_for('main.calculate_result', collection=collection_name))

    elif request.method == 'GET':
        collection_name = request.args.get('collection', None)
        if not collection_name:
            message = "Không tìm thấy dữ liệu"
            return render_template('calculate-result.html', tables='', message=message)
        
        sort_column = request.args.get('sort_column', 'Point Value')
        order = request.args.get('order', 'desc')
        keyword = request.args.get('search_keyword', '').strip()
        
        print(f"Collection Name: {collection_name}")

        filtered_data = list(mongo.db[collection_name].find())    
        if not filtered_data:
            message = "Không có dữ liệu để hiển thị"
            return render_template('calculate-result.html', tables='', message=message)
    
        display_data = pd.DataFrame(filtered_data)
        
        three_months = three_nearest_months(mongo.db[collection_name].find_one())
        
        if keyword:
            display_data = search_keyword(pd.DataFrame(list(mongo.db[collection_name].find())), keyword, threshold=50)
            if display_data.empty:
                message = f"Không tìm thấy kết quả của: '{keyword}'."
                return render_template('calculate-result.html', tables='', message=message, search_keyword=keyword)

        if sort_column in display_data.columns:
            ascending = True if order == 'asc' else False
            display_data = display_data.sort_values(by=sort_column, ascending=ascending)
        
        display_data = display_data[['Keyword', 'Point Value', 'Search Volume (Global)', 'CPC (Global)', 'Competition (Global)', 'Trending %'] + three_months]
        table_html = display_data.to_html(classes='data', index=False)
        return render_template('dashboard-result.html', tables=table_html, message=message, search_keyword=keyword, sort_column=sort_column, order=order)


@main_bp.route('/search', methods=['POST'])
@login_required
def search_view():
    keyword = request.form.get('search_keyword', '').strip()
    collection_name = request.form.get('collection', None) 
    if keyword and collection_name:
        return redirect(url_for('main.calculate_result', search_keyword=keyword, collection=collection_name))
    return redirect(url_for('main.calculate_result'))
import os

@main_bp.route('/download', methods=['GET'])
@login_required
def download_file():
    collection_name = request.args.get('collection', None)
    keyword_limit = request.args.get('keyword_limit_select', 'all') 

    if not collection_name:
        return redirect(url_for('main.calculate_result'))
    
    data = pd.DataFrame(list(mongo.db[collection_name].find()))
    
    original_filename = data['original_filename'].iloc[0] if 'original_filename' in data.columns else 'calculated_data'

    if 'original_filename' in data.columns:
        data = data.drop(columns=['original_filename'])

    if keyword_limit != 'all':
        keyword_limit = int(keyword_limit)
        data = data.head(keyword_limit)

    # Đặt tên file với format: original_filename + "_calculate_" + keyword_limit
    filename = f"{original_filename}_calculate_{keyword_limit}.xlsx"

    output = BytesIO()
    data.to_excel(output, index=False)
    output.seek(0)  

    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@main_bp.route('/all_data', methods=['GET'])
@login_required
def all_data():
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



@main_bp.route('/delete_collection/<collection>', methods=['POST'])
@login_required
def delete_collection(collection):
    mongo.db.drop_collection(collection)
    return redirect(url_for('main.all_data'))

