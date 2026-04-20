# FoodScape - 情绪进食追踪与分析工具

一款基于情绪和环境触发器追踪的心理认知辅助工具，通过数据挖掘无意识进食背后的情境关联，帮助用户以个性化的替代行为打破暴食循环。

## 功能特性

### 📝 极简记录

- **情绪追踪**：8种情绪类型（开心、焦虑、压力、无聊、悲伤、愤怒、平静、疲惫）
- **情境记录**：6种常见情境（工作、学习、家庭、社交、独处、其他）
- **饥饿程度**：5级饥饿度滑块
- **失控标记**：快速标记是否感觉失控
- **可选备注**：记录更多细节

### 📊 智能分析

- **关联规则挖掘**：基于Apriori算法的关联规则分析
- **高风险情境识别**：自动识别导致失控进食的高风险情境组合
- **替代行为建议**：根据情绪和情境提供个性化的替代行为列表
- **统计指标**：支持度、置信度、提升度等专业指标

### 💾 本地存储

- 所有数据轻量存储在本地SQLite数据库
- 无需联网即可使用
- 数据隐私有保障

## 技术架构

### 后端

- **框架**：Python FastAPI
- **数据库**：SQLite + SQLAlchemy ORM
- **数据验证**：Pydantic
- **算法**：关联规则挖掘（Apriori原理）

### 前端

- **UI框架**：Tailwind CSS 3.0
- **交互**：原生JavaScript
- **响应式设计**：支持移动端和桌面端
- **动画效果**：流畅的CSS动画

## 项目结构

```
FoodScape/
├── backend/                 # 后端代码
│   ├── __init__.py
│   ├── database.py         # 数据库配置
│   ├── models.py           # 数据模型
│   ├── schemas.py          # Pydantic模型
│   ├── crud.py             # 数据库操作
│   ├── analysis.py         # 关联算法
│   └── main.py             # FastAPI应用入口
├── frontend/               # 前端代码
│   └── index.html          # 单页面应用
├── requirements.txt        # Python依赖
└── README.md              # 项目说明
```

## 安装与运行

### 环境要求

- Python 3.8+
- pip包管理器

### 安装步骤

1. **克隆项目**

```bash
cd /home/ubuntu/FoodScape
```

1. **创建虚拟环境（推荐）**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

1. **安装依赖**

```bash
pip install -r requirements.txt
```

### 启动应用

**方式一：直接启动**

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**方式二：使用Python模块**

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：

- 应用页面：<http://localhost:8000>
- API文档：<http://localhost:8000/docs>
- 自动文档：<http://localhost:8000/redoc>

## 使用指南

### 1. 记录进食

打开应用，默认进入「记录」页面

- 选择当前的情绪状态
- 选择当前所处的情境
- 滑动饥饿程度滑块
- 切换是否感觉失控
- （可选）添加备注
- 点击「保存记录」

### 2. 查看历史

1. 切换到「历史」标签页
2. 查看所有记录的列表
3. 每条记录显示：情绪、情境、时间、饥饿度、是否失控
4. 点击删除图标可删除记录

### 3. 数据分析

1. 切换到「分析」标签页
2. 查看统计概览（总记录数、失控次数、自控率）
3. 当数据充足时（至少5条记录，其中3条失控），系统会自动分析
4. 查看高风险情境组合，包括：
   - 置信度：该组合导致失控的概率
   - 支持度：该组合出现的频率
   - 提升度：该组合的预测能力
5. 根据建议的替代行为进行行为阻断

## API接口文档

### 记录管理

#### 创建记录

```http
POST /api/records/
Content-Type: application/json

{
    "emotion": "焦虑",
    "situation": "工作",
    "hunger_level": 3,
    "is_out_of_control": true,
    "notes": "赶项目 deadline"
}
```

#### 获取所有记录

```http
GET /api/records/?skip=0&limit=100
```

#### 获取单条记录

```http
GET /api/records/{record_id}
```

#### 更新记录

```http
PUT /api/records/{record_id}
Content-Type: application/json

{
    "notes": "更新的备注"
}
```

#### 删除记录

```http
DELETE /api/records/{record_id}
```

### 分析接口

#### 获取数据分析

```http
GET /api/analysis/
```

响应示例：

```json
{
    "message": "分析完成",
    "total_records": 15,
    "out_of_control_count": 8,
    "high_risk_situations": [
        {
            "situation_combination": "情绪:焦虑 + 情境:工作 → 时间:深夜",
            "count": 5,
            "support": 0.625,
            "confidence": 0.833,
            "lift": 2.5,
            "alternative_behaviors": [
                "深呼吸5次",
                "站起来走5分钟",
                "喝一杯水",
                "写下来你的感受"
            ]
        }
    ]
}
```

#### 获取统计数据

```http
GET /api/stats/
```

## 关联算法说明

### 核心概念

1. **支持度（Support）**：某项集在数据集中出现的频率
   - 公式：Support(A) = 包含A的记录数 / 总记录数
2. **置信度（Confidence）**：在A出现的情况下，B出现的概率
   - 公式：Confidence(A→B) = Support(A∪B) / Support(A)
3. **提升度（Lift）**：衡量A出现对B出现的提升程度
   - 公式：Lift(A→B) = Confidence(A→B) / Support(B)
   - Lift > 1：A对B有正向促进作用
   - Lift = 1：A和B独立
   - Lift < 1：A对B有负向作用

### 算法流程

1. **数据准备**：将失控记录转换为事务集
2. **频繁项集挖掘**：找出出现频率足够高的项集
3. **关联规则生成**：从频繁项集中生成满足最小置信度的规则
4. **规则排序**：按置信度、提升度、支持度排序

## 替代行为策略

根据不同的情绪和情境组合，系统提供个性化的替代行为建议：

| 情绪 | 情境 | 建议行为                  |
| -- | -- | --------------------- |
| 焦虑 | 工作 | 深呼吸、散步、喝水、写感受         |
| 焦虑 | 学习 | 休息、伸展、聊天、听音乐          |
| 压力 | 工作 | 暂停、冥想、深呼吸、泡茶          |
| 压力 | 学习 | 休息、运动、列清单、放松          |
| 无聊 | 晚上 | 看剧、读书、整理、手工           |
| 无聊 | 下午 | 散步、打电话、爱好、家务          |
| 悲伤 | 晚上 | 写日记、看电影、联系支持的人、泡澡     |
| 悲伤 | 独处 | 听音乐、看搞笑视频、写感恩清单、做开心的事 |

## 开发说明

### 添加新的情绪类型

在 `frontend/index.html` 的情绪按钮部分添加新按钮：

```html
<button type="button" data-emotion="新情绪" class="emotion-btn ...">
    <span class="text-3xl mb-2 block">😀</span>
    <span class="font-medium text-gray-700">新情绪</span>
</button>
```

并在 JavaScript 的 `emotionEmojis` 对象中添加对应表情。

### 添加新的替代行为

在 `backend/analysis.py` 的 `ALTERNATIVE_BEHAVIORS` 字典中添加新的组合：

```python
ALTERNATIVE_BEHAVIORS = {
    ("新情绪", "新情境"): ["行为1", "行为2", "行为3"],
    ...
}
```

## 注意事项

1. **数据隐私**：所有数据存储在本地SQLite数据库（`foodscape.db`），不会上传到任何服务器
2. **数据备份**：建议定期备份 `foodscape.db` 文件
3. **分析门槛**：需要至少5条记录且其中3条为失控记录才能进行有效分析
4. **浏览器支持**：推荐使用Chrome、Firefox、Safari等现代浏览器

## 许可证

本项目仅供学习和个人使用。

## 联系

如有问题或建议，请提交Issue。

***

**FoodScape** - 关注你的情绪与进食健康 💜
