from sqlalchemy.orm import Session
from . import models
from collections import defaultdict
from itertools import combinations
from typing import List, Dict, Tuple

ALTERNATIVE_BEHAVIORS = {
    ("焦虑", "工作"): ["深呼吸5次", "站起来走5分钟", "喝一杯水", "写下来你的感受"],
    ("焦虑", "学习"): ["休息10分钟", "做几个伸展运动", "和朋友聊聊天", "听音乐"],
    ("压力", "工作"): ["暂停工作5分钟", "冥想", "做几次深呼吸", "泡一杯茶"],
    ("压力", "学习"): ["离开书桌休息", "做简单的运动", "写待办清单", "给自己5分钟放松"],
    ("无聊", "晚上"): ["看一集短剧集", "读几页书", "整理房间", "做一个小手工"],
    ("无聊", "下午"): ["出门散步", "打电话给朋友", "尝试新的爱好", "做些家务"],
    ("悲伤", "晚上"): ["写日记", "看喜欢的电影", "联系支持你的人", "洗个热水澡"],
    ("悲伤", "独处"): ["听喜欢的音乐", "看搞笑视频", "写感恩清单", "做些让自己开心的事"],
    ("愤怒", "工作"): ["离开冲突环境", "数到10", "做体力活动释放", "写下来你的感受"],
    ("愤怒", "家庭"): ["出去走走", "深呼吸", "写封信但不寄出", "做些消耗精力的事"],
    ("焦虑", "晚上"): ["渐进式肌肉放松", "写担忧清单", "听白噪音", "避免屏幕时间"],
    ("压力", "晚上"): ["做轻松的伸展", "泡温水澡", "读轻松的书", "练习正念呼吸"],
    ("无聊", "工作"): ["喝杯水休息", "拉伸一下", "和同事聊5分钟", "整理办公桌"],
    ("无聊", "学习"): ["换个学习方式", "休息5分钟", "做些小运动", "奖励自己休息"],
}

DEFAULT_BEHAVIORS = [
    "喝一杯水",
    "深呼吸5次",
    "站起来走5分钟",
    "给朋友打个电话",
    "写日记记录感受",
    "做10个简单的伸展动作",
    "听一首喜欢的歌",
    "洗个脸让自己清醒"
]

def get_time_category(hour: int) -> str:
    if 5 <= hour < 12:
        return "早上"
    elif 12 <= hour < 17:
        return "下午"
    elif 17 <= hour < 21:
        return "晚上"
    else:
        return "深夜"

def get_alternative_behaviors(emotion: str, situation: str) -> List[str]:
    key = (emotion, situation)
    if key in ALTERNATIVE_BEHAVIORS:
        return ALTERNATIVE_BEHAVIORS[key]
    
    for (e, s), behaviors in ALTERNATIVE_BEHAVIORS.items():
        if emotion == e or situation == s:
            return behaviors
    
    return DEFAULT_BEHAVIORS

def analyze_associations(db: Session, min_support: float = 0.1, min_confidence: float = 0.3, min_count: int = 3):
    total_records = db.query(models.EatingRecord).count()
    if total_records < 5:
        return {"message": "数据不足，请至少记录5次进食后再进行分析", "high_risk_situations": []}
    
    out_of_control_records = db.query(models.EatingRecord).filter(
        models.EatingRecord.is_out_of_control == True
    ).all()
    
    if len(out_of_control_records) < 3:
        return {
            "message": "失控记录不足，请记录更多失控进食后再进行分析",
            "high_risk_situations": [],
            "total_records": total_records,
            "out_of_control_count": len(out_of_control_records)
        }
    
    transactions = []
    for record in out_of_control_records:
        time_cat = get_time_category(record.timestamp.hour)
        items = [
            f"情绪:{record.emotion}",
            f"情境:{record.situation}",
            f"时间:{time_cat}"
        ]
        transactions.append(items)
    
    item_counts = defaultdict(int)
    for transaction in transactions:
        for item in transaction:
            item_counts[item] += 1
    
    min_item_count = max(min_count, int(len(transactions) * min_support))
    frequent_items = {item: count for item, count in item_counts.items() if count >= min_item_count}
    
    pair_counts = defaultdict(int)
    for transaction in transactions:
        transaction_items = [item for item in transaction if item in frequent_items]
        for pair in combinations(transaction_items, 2):
            pair_key = tuple(sorted(pair))
            pair_counts[pair_key] += 1
    
    frequent_pairs = {pair: count for pair, count in pair_counts.items() if count >= min_item_count}
    
    triple_counts = defaultdict(int)
    for transaction in transactions:
        transaction_items = [item for item in transaction if item in frequent_items]
        for triple in combinations(transaction_items, 3):
            triple_key = tuple(sorted(triple))
            triple_counts[triple_key] += 1
    
    frequent_triples = {triple: count for triple, count in triple_counts.items() if count >= min_item_count}
    
    rules = []
    
    for pair, count in frequent_pairs.items():
        support = count / len(transactions)
        
        for i in range(2):
            antecedent = pair[i]
            consequent = pair[1 - i] if i == 0 else pair[0]
            
            antecedent_count = item_counts[antecedent]
            confidence = count / antecedent_count if antecedent_count > 0 else 0
            
            consequent_support = item_counts[consequent] / len(transactions)
            lift = confidence / consequent_support if consequent_support > 0 else 1
            
            if confidence >= min_confidence:
                rules.append({
                    "combination": f"{antecedent} → {consequent}",
                    "count": count,
                    "support": round(support, 3),
                    "confidence": round(confidence, 3),
                    "lift": round(lift, 3),
                    "items": [antecedent, consequent]
                })
    
    for triple, count in frequent_triples.items():
        support = count / len(transactions)
        
        for i in range(3):
            for j in range(3):
                if i != j:
                    for k in range(3):
                        if k != i and k != j:
                            antecedent = (triple[i], triple[j])
                            consequent = triple[k]
                            
                            antecedent_key = tuple(sorted(antecedent))
                            antecedent_count = pair_counts.get(antecedent_key, 0)
                            if antecedent_count == 0:
                                continue
                            
                            confidence = count / antecedent_count
                            consequent_support = item_counts[consequent] / len(transactions)
                            lift = confidence / consequent_support if consequent_support > 0 else 1
                            
                            if confidence >= min_confidence:
                                rules.append({
                                    "combination": f"{antecedent[0]} + {antecedent[1]} → {consequent}",
                                    "count": count,
                                    "support": round(support, 3),
                                    "confidence": round(confidence, 3),
                                    "lift": round(lift, 3),
                                    "items": list(triple)
                                })
    
    rules = sorted(rules, key=lambda x: (x["confidence"], x["lift"], x["support"]), reverse=True)
    
    high_risk_situations = []
    seen_combinations = set()
    
    for rule in rules[:10]:
        combination_key = rule["combination"]
        if combination_key in seen_combinations:
            continue
        seen_combinations.add(combination_key)
        
        emotion = None
        situation = None
        
        for item in rule["items"]:
            if item.startswith("情绪:"):
                emotion = item.replace("情绪:", "")
            elif item.startswith("情境:"):
                situation = item.replace("情境:", "")
        
        if emotion and situation:
            alternative_behaviors = get_alternative_behaviors(emotion, situation)
        elif emotion:
            alternative_behaviors = get_alternative_behaviors(emotion, "")
        elif situation:
            alternative_behaviors = get_alternative_behaviors("", situation)
        else:
            alternative_behaviors = DEFAULT_BEHAVIORS
        
        high_risk_situations.append({
            "situation_combination": rule["combination"],
            "count": rule["count"],
            "support": rule["support"],
            "confidence": rule["confidence"],
            "lift": rule["lift"],
            "alternative_behaviors": alternative_behaviors
        })
    
    return {
        "message": "分析完成",
        "total_records": total_records,
        "out_of_control_count": len(out_of_control_records),
        "high_risk_situations": high_risk_situations
    }
