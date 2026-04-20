from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from collections import defaultdict

app = Flask(__name__, static_folder='static')
CORS(app)

DATABASE = 'foodscape.db'

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

if __name__ == '__main__':
    init_db()
    print("数据库初始化完成")
    print("启动 FoodScape 应用...")
    print("请在浏览器中访问: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
