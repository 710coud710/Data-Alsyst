import pandas as pd
from fuzzywuzzy import fuzz
from datetime import datetime

def is_similar(keyword1, keyword2, threshold=90):
    return fuzz.ratio(keyword1.lower(), keyword2.lower()) >= threshold

def duplicate_keywords(data):
    unique_keywords = []
    added_keywords = set()  

    for idx1, row1 in data.iterrows():
        keyword1 = row1['Keyword']
        if keyword1 in added_keywords:
            continue  
        
        similar_found = False

        for unique_row in unique_keywords:
            keyword_unique = unique_row['Keyword']
            if is_similar(keyword1, keyword_unique):          
                if are_values_equal(row1, unique_row):
                    similar_found = True
                    added_keywords.add(keyword1)
                    break
        if not similar_found:
            unique_keywords.append(row1)
            added_keywords.add(keyword1)

    return pd.DataFrame(unique_keywords)

def are_values_equal(row1, row2):
    return (row1['Search Volume (Global)'] == row2['Search Volume (Global)'] and
            row1['CPC (Global)'] == row2['CPC (Global)'] and
            row1['Competition (Global)'] == row2['Competition (Global)'])

def calculate_percentile(data, column_name):
    sorted_data = sorted(data[column_name])
    n = len(sorted_data)
    percentiles = []
    for value in data[column_name]:
        r = sorted_data.index(value) + 1  
        k = ((r-0.5) / n) * 100
        percentiles.append(k)
    return percentiles

def ensure_string_keys(doc):
    new_doc = {}
    for key, value in doc.items():
        new_key = str(key) if not isinstance(key, str) else key
        new_doc[new_key] = value
    return new_doc

def ensure_timestamp_keys(doc):
    new_doc = {}
    for key, value in doc.items():
        if isinstance(key, datetime):
            new_key = str(int(key.timestamp()))
        else:
            new_key = str(key) if not isinstance(key, str) else key
        new_doc[new_key] = value
    return new_doc

def calculate_point_value(data):
    search_value = data['Search Volume Percentile'] * 1
    cpc_value = 100 - (data['CPC Percentile'] * 1)
    competition_value = 100 - (data['Competition Percentile'] * 1)
    data['Point Value'] = (search_value + cpc_value + competition_value) / 3
    return data

def search_keyword(data, keyword, threshold=70):
    results = []
    for idx, row in data.iterrows():
        if is_similar(row['Keyword'], keyword, threshold):
            results.append(row)
    return pd.DataFrame(results)

def convert_datetime_string(data):
    new_doc = {}
    for key in data.keys():
        try:
            new_key = datetime.strptime(key, '%Y-%m-%d')
        except ValueError:
            new_key = key
        new_doc[new_key] = data[key]
    return new_doc

def convert_string_datetime(data):
    new_doc = {}
    for key, value in data.items():
        try:
            new_key = datetime.strptime(key, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                new_key = datetime.strptime(key, '%Y-%m-%d')
            except ValueError:
                new_key = key
        new_doc[new_key] = value
    
    return new_doc

def three_nearest_months(data):
    converted_data = convert_string_datetime(data)

    date_columns = [key for key in converted_data.keys() if isinstance(key, datetime)]
    if not date_columns:
        print("Không tìm thấy")

    sorted_date_columns = sorted(date_columns, key=lambda x: abs(x - datetime.now()))

    nearest_date_columns = sorted_date_columns[:3]
    
    return [col.strftime('%Y-%m-%d %H:%M:%S') for col in nearest_date_columns]

# def is_date_string(column_name):
#     try:
#         pd.to_datetime(column_name, format='%Y-%m-%d', errors='raise')
#         return True
#     except (ValueError, TypeError):
#         return False