from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
from collections import defaultdict
import json
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__, static_folder='static')
CORS(app)

DATABASE = 'foodscape.db'

FOOD_DATABASE = {
    '苹果': {'calories': 52, 'carbs': 14, 'protein': 0.3, 'fat': 0.2, 'unit': '个(约180g)'},
    '香蕉': {'calories': 89, 'carbs': 23, 'protein': 1.1, 'fat': 0.3, 'unit': '根(约120g)'},
    '米饭': {'calories': 130, 'carbs': 28, 'protein': 2.7, 'fat': 0.3, 'unit': '碗(约100g)'},
    '面条': {'calories': 117, 'carbs': 25, 'protein': 3.8, 'fat': 0.5, 'unit': '碗(约100g)'},
    '鸡蛋': {'calories': 78, 'carbs': 0.6, 'protein': 6, 'fat': 5, 'unit': '个(约50g)'},
    '牛奶': {'calories': 42, 'carbs': 5, 'protein': 3.4, 'fat': 1, 'unit': '杯(约250ml)'},
    '面包': {'calories': 265, 'carbs': 49, 'protein': 9, 'fat': 3.2, 'unit': '片(约30g)'},
    '鸡肉': {'calories': 165, 'carbs': 0, 'protein': 31, 'fat': 3.6, 'unit': '块(约100g)'},
    '牛肉': {'calories': 250, 'carbs': 0, 'protein': 26, 'fat': 15, 'unit': '块(约100g)'},
    '鱼肉': {'calories': 206, 'carbs': 0, 'protein': 22, 'fat': 12, 'unit': '块(约100g)'},
    '猪肉': {'calories': 242, 'carbs': 0, 'protein': 27, 'fat': 14, 'unit': '块(约100g)'},
    '土豆': {'calories': 77, 'carbs': 17, 'protein': 2, 'fat': 0.1, 'unit': '个(约170g)'},
    '西红柿': {'calories': 18, 'carbs': 3.9, 'protein': 0.9, 'fat': 0.2, 'unit': '个(约120g)'},
    '黄瓜': {'calories': 16, 'carbs': 3.6, 'protein': 0.7, 'fat': 0.1, 'unit': '根(约100g)'},
    '胡萝卜': {'calories': 41, 'carbs': 10, 'protein': 0.9, 'fat': 0.2, 'unit': '根(约60g)'},
    '西兰花': {'calories': 34, 'carbs': 7, 'protein': 2.8, 'fat': 0.4, 'unit': '朵(约100g)'},
    '橙子': {'calories': 47, 'carbs': 12, 'protein': 0.9, 'fat': 0.1, 'unit': '个(约130g)'},
    '葡萄': {'calories': 69, 'carbs': 18, 'protein': 0.7, 'fat': 0.2, 'unit': '串(约100g)'},
    '西瓜': {'calories': 30, 'carbs': 8, 'protein': 0.6, 'fat': 0.2, 'unit': '块(约100g)'},
    '冰淇淋': {'calories': 207, 'carbs': 24, 'protein': 3.5, 'fat': 11, 'unit': '份(约100g)'},
    '巧克力': {'calories': 546, 'carbs': 61, 'protein': 4.6, 'fat': 31, 'unit': '块(约100g)'},
    '蛋糕': {'calories': 267, 'carbs': 47, 'protein': 3.7, 'fat': 8.2, 'unit': '块(约100g)'},
    '饼干': {'calories': 456, 'carbs': 72, 'protein': 6.5, 'fat': 16, 'unit': '包(约100g)'},
    '薯片': {'calories': 536, 'carbs': 53, 'protein': 6.3, 'fat': 35, 'unit': '包(约100g)'},
    '可乐': {'calories': 42, 'carbs': 11, 'protein': 0, 'fat': 0, 'unit': '罐(约330ml)'},
    '咖啡': {'calories': 2, 'carbs': 0, 'protein': 0.3, 'fat': 0, 'unit': '杯(约250ml)'},
    '茶': {'calories': 1, 'carbs': 0, 'protein': 0.1, 'fat': 0, 'unit': '杯(约250ml)'},
    '啤酒': {'calories': 43, 'carbs': 3.6, 'protein': 0.5, 'fat': 0, 'unit': '瓶(约330ml)'},
    '红酒': {'calories': 85, 'carbs': 2.6, 'protein': 0.1, 'fat': 0, 'unit': '杯(约150ml)'},
}

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            emotion TEXT NOT NULL,
            situation TEXT NOT NULL,
            hunger_level INTEGER NOT NULL,
            is_out_of_control INTEGER NOT NULL,
            notes TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            food_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT NOT NULL,
            calories REAL NOT NULL,
            carbs REAL NOT NULL,
            protein REAL NOT NULL,
            fat REAL NOT NULL,
            meal_type TEXT NOT NULL,
            notes TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/records', methods=['GET'])
def get_records():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM records ORDER BY timestamp DESC')
    records = cursor.fetchall()
    conn.close()
    
    result = []
    for record in records:
        result.append({
            'id': record['id'],
            'timestamp': record['timestamp'],
            'emotion': record['emotion'],
            'situation': record['situation'],
            'hunger_level': record['hunger_level'],
            'is_out_of_control': bool(record['is_out_of_control']),
            'notes': record['notes']
        })
    
    return jsonify(result)

@app.route('/api/records', methods=['POST'])
def create_record():
    data = request.json
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO records (timestamp, emotion, situation, hunger_level, is_out_of_control, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        data['emotion'],
        data['situation'],
        data['hunger_level'],
        1 if data['is_out_of_control'] else 0,
        data.get('notes', '')
    ))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'id': record_id, 'message': 'Record created successfully'}), 201

@app.route('/api/records/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM records WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Record deleted successfully'})

@app.route('/api/analysis', methods=['GET'])
def analyze_patterns():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM records')
    records = cursor.fetchall()
    conn.close()
    
    if len(records) < 5:
        return jsonify({
            'message': '需要更多数据才能进行分析（至少需要5条记录）',
            'total_records': len(records),
            'high_risk_combinations': [],
            'recommendations': []
        })
    
    out_of_control_records = [r for r in records if r['is_out_of_control'] == 1]
    
    if len(out_of_control_records) == 0:
        return jsonify({
            'message': '目前还没有失控进食的记录',
            'total_records': len(records),
            'high_risk_combinations': [],
            'recommendations': []
        })
    
    pattern_counts = defaultdict(int)
    emotion_situation_counts = defaultdict(int)
    situation_counts = defaultdict(int)
    emotion_counts = defaultdict(int)
    
    for record in out_of_control_records:
        emotion = record['emotion']
        situation = record['situation']
        hour = datetime.fromisoformat(record['timestamp']).hour
        
        time_category = '深夜' if 22 <= hour or hour < 6 else \
                         '早晨' if 6 <= hour < 10 else \
                         '中午' if 10 <= hour < 14 else \
                         '下午' if 14 <= hour < 18 else '傍晚'
        
        key = (emotion, situation, time_category)
        pattern_counts[key] += 1
        
        emotion_situation_key = (emotion, situation)
        emotion_situation_counts[emotion_situation_key] += 1
        
        situation_counts[situation] += 1
        emotion_counts[emotion] += 1
    
    high_risk_combinations = []
    
    for (emotion, situation, time), count in pattern_counts.items():
        if count >= 2:
            high_risk_combinations.append({
                'emotion': emotion,
                'situation': situation,
                'time': time,
                'count': count,
                'percentage': round(count / len(out_of_control_records) * 100, 1)
            })
    
    high_risk_combinations.sort(key=lambda x: x['count'], reverse=True)
    
    recommendations = []
    
    for combo in high_risk_combinations[:3]:
        recs = get_recommendations_for_pattern(combo['emotion'], combo['situation'])
        recommendations.append({
            'pattern': combo,
            'alternatives': recs
        })
    
    return jsonify({
        'total_records': len(records),
        'out_of_control_records': len(out_of_control_records),
        'high_risk_combinations': high_risk_combinations,
        'recommendations': recommendations,
        'statistics': {
            'top_emotions': sorted(
                [{'emotion': e, 'count': c} for e, c in emotion_counts.items()],
                key=lambda x: x['count'], reverse=True
            )[:5],
            'top_situations': sorted(
                [{'situation': s, 'count': c} for s, c in situation_counts.items()],
                key=lambda x: x['count'], reverse=True
            )[:5]
        }
    })

def get_recommendations_for_pattern(emotion, situation):
    base_recommendations = {
        '焦虑': [
            '深呼吸练习：4-7-8呼吸法',
            '5-4-3-2-1感官接地练习',
            '出去散步5-10分钟',
            '喝一杯温水',
            '写下来你的感受和担忧',
            '做一些简单的拉伸运动'
        ],
        '压力': [
            '渐进式肌肉放松',
            '听舒缓的音乐',
            '与朋友或家人聊聊',
            '暂时离开压力环境',
            '做10分钟的冥想',
            '看一些有趣的视频'
        ],
        '无聊': [
            '找一项有趣的活动',
            '阅读一本书',
            '做一些手工或创意活动',
            '给朋友打电话',
            '出去走走',
            '做一些轻度运动'
        ],
        '悲伤': [
            '允许自己感受情绪，不要压抑',
            '写日记表达感受',
            '与信任的人交谈',
            '做一些能让自己稍微开心的事',
            '照顾好自己的身体',
            '看看以前的美好照片'
        ],
        '愤怒': [
            '数到10再做任何决定',
            '离开当前环境冷静一下',
            '做一些体力活动释放情绪',
            '写下来你的愤怒（不用发送）',
            '深呼吸',
            '尝试理解愤怒背后的真正原因'
        ],
        '疲惫': [
            '休息5-10分钟',
            '如果可能的话小睡一会儿',
            '喝一杯水或茶',
            '做一些简单的伸展',
            '调整你的计划，降低要求',
            '呼吸新鲜空气'
        ],
        '兴奋': [
            '把能量引导到其他活动',
            '做一些有趣但不涉及食物的事',
            '与朋友分享你的兴奋',
            '写下来让你兴奋的事',
            '出去走走消耗一些能量',
            '做一些创造性的活动'
        ],
        '平静': [
            '享受当下的平静',
            '做一些你喜欢的事情',
            '阅读或听音乐',
            '出去散步',
            '做一些轻度运动',
            '与朋友聊天'
        ]
    }
    
    situation_specific = {
        '工作学习': [
            '设置番茄钟，每25分钟休息5分钟',
            '起来活动一下',
            '喝杯水',
            '看窗外几分钟',
            '做一些简单的眼部放松',
            '整理一下桌面'
        ],
        '休闲娱乐': [
            '选择一种不涉及食物的娱乐方式',
            '玩个游戏',
            '看集喜欢的节目',
            '做一些手工',
            '出去散步',
            '与朋友视频聊天'
        ],
        '社交场合': [
            '与他人交谈转移注意力',
            '喝水而不是吃东西',
            '参与活动而不是关注食物',
            '提前计划好替代行为',
            '与信任的人分享你的目标',
            '专注于社交互动本身'
        ],
        '独处': [
            '做一些你喜欢的独处活动',
            '阅读',
            '听音乐',
            '冥想',
            '写日记',
            '做一些创造性的事情'
        ],
        '通勤': [
            '听音乐或播客',
            '观察窗外的风景',
            '做一些简单的呼吸练习',
            '计划一下当天的事情',
            '玩个简单的手机游戏',
            '与朋友发消息聊天'
        ],
        '睡前': [
            '做一些放松的活动',
            '阅读纸质书',
            '做渐进式肌肉放松',
            '听舒缓的音乐或白噪音',
            '避免使用电子设备',
            '写下来明天的计划'
        ]
    }
    
    emotion_recs = base_recommendations.get(emotion, [])
    situation_recs = situation_specific.get(situation, [])
    
    combined = emotion_recs + situation_recs
    unique_recs = list(dict.fromkeys(combined))
    
    return unique_recs[:8]

@app.route('/api/foods', methods=['GET'])
def get_food_list():
    food_list = []
    for name, info in FOOD_DATABASE.items():
        food_list.append({
            'name': name,
            'calories': info['calories'],
            'carbs': info['carbs'],
            'protein': info['protein'],
            'fat': info['fat'],
            'unit': info['unit']
        })
    return jsonify(food_list)

@app.route('/api/food-records', methods=['GET'])
def get_food_records():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM food_records ORDER BY timestamp DESC')
    records = cursor.fetchall()
    conn.close()
    
    result = []
    for record in records:
        result.append({
            'id': record['id'],
            'timestamp': record['timestamp'],
            'food_name': record['food_name'],
            'quantity': record['quantity'],
            'unit': record['unit'],
            'calories': record['calories'],
            'carbs': record['carbs'],
            'protein': record['protein'],
            'fat': record['fat'],
            'meal_type': record['meal_type'],
            'notes': record['notes']
        })
    
    return jsonify(result)

@app.route('/api/food-records', methods=['POST'])
def create_food_record():
    data = request.json
    
    food_name = data['food_name']
    quantity = data['quantity']
    
    if food_name not in FOOD_DATABASE:
        return jsonify({'error': '食物类型不存在'}), 400
    
    food_info = FOOD_DATABASE[food_name]
    calories = food_info['calories'] * quantity
    carbs = food_info['carbs'] * quantity
    protein = food_info['protein'] * quantity
    fat = food_info['fat'] * quantity
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO food_records (timestamp, food_name, quantity, unit, calories, carbs, protein, fat, meal_type, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        food_name,
        quantity,
        food_info['unit'],
        calories,
        carbs,
        protein,
        fat,
        data['meal_type'],
        data.get('notes', '')
    ))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    
    return jsonify({
        'id': record_id, 
        'message': '食物记录创建成功',
        'nutrition': {
            'calories': calories,
            'carbs': carbs,
            'protein': protein,
            'fat': fat
        }
    }), 201

@app.route('/api/food-records/<int:record_id>', methods=['DELETE'])
def delete_food_record(record_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM food_records WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': '食物记录删除成功'})

@app.route('/api/nutrition-analysis', methods=['GET'])
def nutrition_analysis():
    period = request.args.get('period', 'day')
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now()
    if period == 'day':
        start_time = now - timedelta(days=1)
    elif period == 'week':
        start_time = now - timedelta(weeks=1)
    elif period == 'month':
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(days=1)
    
    cursor.execute('''
        SELECT * FROM food_records WHERE timestamp >= ? ORDER BY timestamp
    ''', (start_time.isoformat(),))
    records = cursor.fetchall()
    conn.close()
    
    total_calories = sum(r['calories'] for r in records)
    total_carbs = sum(r['carbs'] for r in records)
    total_protein = sum(r['protein'] for r in records)
    total_fat = sum(r['fat'] for r in records)
    
    daily_records = defaultdict(lambda: {'calories': 0, 'carbs': 0, 'protein': 0, 'fat': 0})
    meal_records = defaultdict(lambda: {'calories': 0, 'count': 0})
    
    for record in records:
        date = record['timestamp'].split('T')[0]
        daily_records[date]['calories'] += record['calories']
        daily_records[date]['carbs'] += record['carbs']
        daily_records[date]['protein'] += record['protein']
        daily_records[date]['fat'] += record['fat']
        
        meal_type = record['meal_type']
        meal_records[meal_type]['calories'] += record['calories']
        meal_records[meal_type]['count'] += 1
    
    daily_data = []
    for date, data in sorted(daily_records.items()):
        daily_data.append({
            'date': date,
            'calories': round(data['calories'], 1),
            'carbs': round(data['carbs'], 1),
            'protein': round(data['protein'], 1),
            'fat': round(data['fat'], 1)
        })
    
    meal_data = []
    for meal_type, data in meal_records.items():
        meal_data.append({
            'meal_type': meal_type,
            'total_calories': round(data['calories'], 1),
            'average_calories': round(data['calories'] / data['count'], 1) if data['count'] > 0 else 0
        })
    
    return jsonify({
        'period': period,
        'summary': {
            'total_calories': round(total_calories, 1),
            'total_carbs': round(total_carbs, 1),
            'total_protein': round(total_protein, 1),
            'total_fat': round(total_fat, 1),
            'average_daily_calories': round(total_calories / len(daily_records), 1) if daily_records else 0
        },
        'daily_data': daily_data,
        'meal_breakdown': meal_data
    })

@app.route('/api/trends/emotion', methods=['GET'])
def emotion_trends():
    period = request.args.get('period', 'week')
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now()
    if period == 'week':
        start_time = now - timedelta(weeks=1)
    elif period == 'month':
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(weeks=1)
    
    cursor.execute('''
        SELECT * FROM records WHERE timestamp >= ? ORDER BY timestamp
    ''', (start_time.isoformat(),))
    records = cursor.fetchall()
    conn.close()
    
    emotion_map = {
        '焦虑': 1, '压力': 2, '无聊': 3, '悲伤': 4,
        '愤怒': 5, '疲惫': 6, '兴奋': 7, '平静': 8
    }
    
    daily_emotions = defaultdict(list)
    for record in records:
        date = record['timestamp'].split('T')[0]
        daily_emotions[date].append(record['emotion'])
    
    trend_data = []
    for date, emotions in sorted(daily_emotions.items()):
        emotion_counts = defaultdict(int)
        for e in emotions:
            emotion_counts[e] += 1
        
        dominant_emotion = max(emotion_counts.keys(), key=lambda x: emotion_counts[x])
        
        trend_data.append({
            'date': date,
            'dominant_emotion': dominant_emotion,
            'emotion_counts': dict(emotion_counts),
            'total_records': len(emotions)
        })
    
    return jsonify({
        'period': period,
        'trend_data': trend_data,
        'total_records': len(records)
    })

@app.route('/api/trends/out-of-control', methods=['GET'])
def out_of_control_trends():
    period = request.args.get('period', 'week')
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now()
    if period == 'week':
        start_time = now - timedelta(weeks=1)
    elif period == 'month':
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(weeks=1)
    
    cursor.execute('''
        SELECT * FROM records WHERE timestamp >= ? ORDER BY timestamp
    ''', (start_time.isoformat(),))
    records = cursor.fetchall()
    conn.close()
    
    daily_stats = defaultdict(lambda: {'total': 0, 'out_of_control': 0})
    hourly_stats = defaultdict(lambda: {'total': 0, 'out_of_control': 0})
    weekday_stats = defaultdict(lambda: {'total': 0, 'out_of_control': 0})
    
    for record in records:
        timestamp = datetime.fromisoformat(record['timestamp'])
        date = record['timestamp'].split('T')[0]
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        daily_stats[date]['total'] += 1
        hourly_stats[hour]['total'] += 1
        weekday_stats[weekday]['total'] += 1
        
        if record['is_out_of_control'] == 1:
            daily_stats[date]['out_of_control'] += 1
            hourly_stats[hour]['out_of_control'] += 1
            weekday_stats[weekday]['out_of_control'] += 1
    
    daily_data = []
    for date, stats in sorted(daily_stats.items()):
        daily_data.append({
            'date': date,
            'total': stats['total'],
            'out_of_control': stats['out_of_control'],
            'rate': round(stats['out_of_control'] / stats['total'] * 100, 1) if stats['total'] > 0 else 0
        })
    
    hourly_data = []
    for hour in range(24):
        stats = hourly_stats[hour]
        hourly_data.append({
            'hour': hour,
            'total': stats['total'],
            'out_of_control': stats['out_of_control'],
            'rate': round(stats['out_of_control'] / stats['total'] * 100, 1) if stats['total'] > 0 else 0
        })
    
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday_data = []
    for i in range(7):
        stats = weekday_stats[i]
        weekday_data.append({
            'weekday': weekday_names[i],
            'total': stats['total'],
            'out_of_control': stats['out_of_control'],
            'rate': round(stats['out_of_control'] / stats['total'] * 100, 1) if stats['total'] > 0 else 0
        })
    
    return jsonify({
        'period': period,
        'daily_data': daily_data,
        'hourly_data': hourly_data,
        'weekday_data': weekday_data,
        'summary': {
            'total_records': len(records),
            'total_out_of_control': sum(1 for r in records if r['is_out_of_control'] == 1)
        }
    })

@app.route('/api/trends/situation-heatmap', methods=['GET'])
def situation_heatmap():
    period = request.args.get('period', 'week')
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now()
    if period == 'week':
        start_time = now - timedelta(weeks=1)
    elif period == 'month':
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(weeks=1)
    
    cursor.execute('''
        SELECT * FROM records WHERE timestamp >= ? ORDER BY timestamp
    ''', (start_time.isoformat(),))
    records = cursor.fetchall()
    conn.close()
    
    heatmap_data = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'out_of_control': 0}))
    emotions = ['焦虑', '压力', '无聊', '悲伤', '愤怒', '疲惫', '兴奋', '平静']
    situations = ['工作学习', '休闲娱乐', '社交场合', '独处', '通勤', '睡前']
    
    for record in records:
        emotion = record['emotion']
        situation = record['situation']
        
        heatmap_data[emotion][situation]['total'] += 1
        if record['is_out_of_control'] == 1:
            heatmap_data[emotion][situation]['out_of_control'] += 1
    
    matrix = []
    for emotion in emotions:
        row = {'emotion': emotion}
        for situation in situations:
            data = heatmap_data[emotion][situation]
            row[situation] = {
                'total': data['total'],
                'out_of_control': data['out_of_control'],
                'rate': round(data['out_of_control'] / data['total'] * 100, 1) if data['total'] > 0 else 0
            }
        matrix.append(row)
    
    return jsonify({
        'period': period,
        'heatmap_matrix': matrix,
        'emotions': emotions,
        'situations': situations
    })

@app.route('/api/export/json', methods=['GET'])
def export_json():
    report_type = request.args.get('type', 'weekly')
    
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now()
    if report_type == 'weekly':
        start_time = now - timedelta(weeks=1)
        report_title = '每周报告'
    elif report_type == 'monthly':
        start_time = now - timedelta(days=30)
        report_title = '每月报告'
    else:
        start_time = now - timedelta(weeks=1)
        report_title = '每周报告'
    
    cursor.execute('SELECT * FROM records WHERE timestamp >= ? ORDER BY timestamp', (start_time.isoformat(),))
    records = cursor.fetchall()
    
    cursor.execute('SELECT * FROM food_records WHERE timestamp >= ? ORDER BY timestamp', (start_time.isoformat(),))
    food_records = cursor.fetchall()
    conn.close()
    
    records_list = []
    for r in records:
        records_list.append({
            'id': r['id'],
            'timestamp': r['timestamp'],
            'emotion': r['emotion'],
            'situation': r['situation'],
            'hunger_level': r['hunger_level'],
            'is_out_of_control': bool(r['is_out_of_control']),
            'notes': r['notes']
        })
    
    food_list = []
    for f in food_records:
        food_list.append({
            'id': f['id'],
            'timestamp': f['timestamp'],
            'food_name': f['food_name'],
            'quantity': f['quantity'],
            'unit': f['unit'],
            'calories': f['calories'],
            'carbs': f['carbs'],
            'protein': f['protein'],
            'fat': f['fat'],
            'meal_type': f['meal_type'],
            'notes': f['notes']
        })
    
    total_calories = sum(f['calories'] for f in food_records)
    total_carbs = sum(f['carbs'] for f in food_records)
    total_protein = sum(f['protein'] for f in food_records)
    total_fat = sum(f['fat'] for f in food_records)
    
    out_of_control_count = sum(1 for r in records if r['is_out_of_control'] == 1)
    
    report = {
        'report_type': report_type,
        'report_title': report_title,
        'generated_at': now.isoformat(),
        'period': {
            'start': start_time.isoformat(),
            'end': now.isoformat()
        },
        'summary': {
            'total_emotion_records': len(records),
            'total_food_records': len(food_records),
            'out_of_control_count': out_of_control_count,
            'out_of_control_rate': round(out_of_control_count / len(records) * 100, 1) if records else 0,
            'nutrition': {
                'total_calories': round(total_calories, 1),
                'total_carbs': round(total_carbs, 1),
                'total_protein': round(total_protein, 1),
                'total_fat': round(total_fat, 1)
            }
        },
        'emotion_records': records_list,
        'food_records': food_list
    }
    
    return jsonify(report)

@app.route('/api/export/pdf', methods=['GET'])
def export_pdf():
    report_type = request.args.get('type', 'weekly')
    
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now()
    if report_type == 'weekly':
        start_time = now - timedelta(weeks=1)
        report_title = 'FoodScape 每周报告'
    elif report_type == 'monthly':
        start_time = now - timedelta(days=30)
        report_title = 'FoodScape 每月报告'
    else:
        start_time = now - timedelta(weeks=1)
        report_title = 'FoodScape 每周报告'
    
    cursor.execute('SELECT * FROM records WHERE timestamp >= ? ORDER BY timestamp', (start_time.isoformat(),))
    records = cursor.fetchall()
    
    cursor.execute('SELECT * FROM food_records WHERE timestamp >= ? ORDER BY timestamp', (start_time.isoformat(),))
    food_records = cursor.fetchall()
    conn.close()
    
    total_calories = sum(f['calories'] for f in food_records)
    total_carbs = sum(f['carbs'] for f in food_records)
    total_protein = sum(f['protein'] for f in food_records)
    total_fat = sum(f['fat'] for f in food_records)
    out_of_control_count = sum(1 for r in records if r['is_out_of_control'] == 1)
    
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
        font_name = 'STSong-Light'
    except:
        try:
            font_paths = [
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            ]
            
            font_name = 'ChineseFont'
            font_registered = False
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        font_registered = True
                        break
                    except:
                        continue
            
            if not font_registered:
                font_name = 'Helvetica'
        except:
            font_name = 'Helvetica'
    
    pdf_buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontName=font_name,
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=16,
        spaceBefore=20,
        spaceAfter=15,
        textColor=colors.HexColor('#34495e'),
        borderPadding=(0, 0, 5, 0),
        borderWidth=0,
        borderColor=colors.HexColor('#3498db')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        spaceAfter=10,
        leading=18
    )
    
    small_style = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        textColor=colors.gray
    )
    
    story = []
    
    story.append(Paragraph(report_title, title_style))
    story.append(Paragraph(f'生成时间: {now.strftime("%Y-%m-%d %H:%M:%S")}', small_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph('报告摘要', heading_style))
    
    summary_data = [
        ['情绪记录总数', f'{len(records)} 条'],
        ['食物记录总数', f'{len(food_records)} 条'],
        ['失控进食次数', f'{out_of_control_count} 次'],
        ['失控进食率', f'{round(out_of_control_count / len(records) * 100, 1) if records else 0}%'],
    ]
    
    summary_table = Table(summary_data, colWidths=[8*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(summary_table)
    
    story.append(Paragraph('营养摄入统计', heading_style))
    
    nutrition_data = [
        ['总卡路里', f'{round(total_calories, 1)} kcal'],
        ['总碳水化合物', f'{round(total_carbs, 1)} g'],
        ['总蛋白质', f'{round(total_protein, 1)} g'],
        ['总脂肪', f'{round(total_fat, 1)} g'],
    ]
    
    nutrition_table = Table(nutrition_data, colWidths=[8*cm, 6*cm])
    nutrition_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(nutrition_table)
    
    story.append(Paragraph('食物记录详情', heading_style))
    
    if food_records:
        food_table_data = [['时间', '食物名称', '分量', '餐次', '卡路里']]
        
        for food in food_records:
            timestamp = datetime.fromisoformat(food['timestamp']).strftime('%Y-%m-%d %H:%M')
            food_table_data.append([
                timestamp,
                food['food_name'],
                f'{food["quantity"]} {food["unit"]}',
                food['meal_type'],
                f'{round(food["calories"], 1)} kcal'
            ])
        
        food_table = Table(food_table_data, colWidths=[3.5*cm, 3*cm, 3*cm, 2*cm, 2.5*cm])
        food_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        for i in range(1, len(food_table_data)):
            if i % 2 == 0:
                food_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')),
                ]))
        
        story.append(food_table)
    else:
        story.append(Paragraph('暂无食物记录', normal_style))
    
    story.append(Paragraph('情绪记录详情', heading_style))
    
    if records:
        emotion_table_data = [['时间', '情绪', '情境', '饥饿程度', '失控进食']]
        
        for record in records:
            timestamp = datetime.fromisoformat(record['timestamp']).strftime('%Y-%m-%d %H:%M')
            is_out_of_control = '是' if record['is_out_of_control'] == 1 else '否'
            emotion_table_data.append([
                timestamp,
                record['emotion'],
                record['situation'],
                str(record['hunger_level']),
                is_out_of_control
            ])
        
        emotion_table = Table(emotion_table_data, colWidths=[3.5*cm, 2.5*cm, 2.5*cm, 2*cm, 2.5*cm])
        emotion_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        for i in range(1, len(emotion_table_data)):
            if i % 2 == 0:
                emotion_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')),
                ]))
        
        for i, row in enumerate(emotion_table_data[1:], start=1):
            if row[4] == '是':
                emotion_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fff3cd')),
                ]))
        
        story.append(emotion_table)
    else:
        story.append(Paragraph('暂无情绪记录', normal_style))
    
    story.append(Spacer(1, 30))
    story.append(Paragraph('FoodScape - 关注健康饮食，了解自己的进食习惯', small_style))
    story.append(Paragraph('本报告由 FoodScape 系统自动生成', small_style))
    
    doc.build(story)
    pdf_buffer.seek(0)
    
    filename = f'foodscape-{report_type}-report-{now.strftime("%Y%m%d")}.pdf'
    
    return send_file(
        pdf_buffer,
        download_name=filename,
        as_attachment=True,
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    init_db()
    print("数据库初始化完成")
    print("启动 FoodScape 应用...")
    print("请在浏览器中访问: http://localhost:8562")
    app.run(debug=True, host='0.0.0.0', port=8562)
