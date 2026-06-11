# Questionnaire Templates
# 三套问卷模板：1分钟极速版 / 3分钟快速版 / 7步完整版

## 1 Minute Ultra-Quick Version

**Use case**: Emergency situations, very limited time

```
╔═══════════════════════════════════════════════════════════════════╗
║              ⚡ 高考志愿 - 1分钟极速版                              ║
╚════════════════════════════════━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━═══╝

请直接回复以下信息（空格分隔）：

姓名 省份 分数 位次 类型 不能接受的

类型说明（选1个字母）：
R=动手型(计算机/电子/机械)
I=研究型(数学/物理/医学)
A=艺术型(设计/建筑/传媒)
S=助人型(师范/医学/心理)
E=管理型(经济/金融/管理)
C=常规型(会计/统计/财务)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
示例回复：
李明 浙江 612 15230 R 社交
```

## 3 Minute Quick Version

**Use case**: Standard consultation, balance between speed and completeness

```
╔═══════════════════════════════════════════════════════════════════╗
║              ⚡ 高考志愿填报 - 3分钟快速问卷                        ║
╚═══════════════════════════════════════════════════════════════════╝

【必填 - 基本信息】
1. 考生姓名：___________
2. 所在省份：___________
3. 高考总分：_____分
4. 全省位次：_____名（查一分一段表）

【必填 - 核心匹配】
5. 你是哪种类型？（选1个字母）
   R. 🔧 喜欢动手拆装修东西 → 计算机、电子、机械
   I. 🔬 喜欢研究探索 → 数学、物理、医学
   A. 🎨 喜欢创意创作 → 设计、建筑、传媒
   S. 🤝 喜欢帮助人 → 师范、医学、心理学
   E. 📊 喜欢领导组织 → 管理、经济、金融
   C. 📝 喜欢规范有序 → 会计、统计、财务

6. 最擅长哪2门？（如：物理、数学）
7. 明确不喜欢的？（背诵/数学/社交/实验/代码）

【选填 - 关键约束】
8. 经济条件：①困难 ②一般 ③中等 ④较好
9. 毕业规划：①就业 ②考研 ③考公 ④不确定
10. 工作地点：①一线 ②新一线 ③本省 ④都能接受
```

## 7 Step Complete Version

**Use case**: Deep planning, maximum accuracy

### Step 1: Basic Information
- Name
- Province
- Contact phone (optional)

### Step 2: Exam Information
- Test mode (Traditional / 3+3 / 3+1+2)
- Subject selection
- Total score (0-750)
- Province rank (must be positive integer)
- Subject scores (optional)

### Step 3: Interest Assessment (Holland Codes)

**Question 1**: What do you like doing in free time?
- A. Taking things apart/assembling → R (Realistic)
- B. Reading/researching → I (Investigative)
- C. Drawing/designing/creating → A (Artistic)
- D. Hanging out with friends → S (Social)
- E. Doing business/organizing → E (Enterprising)
- F. Organizing/planning → C (Conventional)

**Question 2**: If money was no object, what would you do?
(Same options map to same Holland codes)

**Question 3**: What activities make you lose track of time?
(Same options)

**Question 4**: What do you definitely dislike? (Multi-select)
- A. Memorization → Avoid: Law, Medicine, Humanities
- B. Math/Calculation → Avoid: Finance, CS, Engineering
- C. Social interaction → Avoid: Marketing, Management, Teaching
- D. Experiments/Hands-on → Avoid: Chemistry, Biology, Materials
- E. Coding → Avoid: Computer Science, Software
- F. None/I like everything

Scoring: Count responses per type (R/I/A/S/E/C)
Primary type = highest count
Secondary type = second highest

### Step 4: Ability Assessment

**Subject Scores** (Rate 1-5):
| Subject | Score |
|---------|-------|
| Math    | __    |
| Physics | __    |
| Chemistry | __  |
| Biology | __    |
| Chinese | __    |
| English | __    |

Scale: 1=Very Weak, 2=Weak, 3=Average, 4=Strong, 5=Very Strong

**Soft Skills** (Rate 1-5):
- Logical thinking
- Hands-on ability
- Communication
- Organization/Coordination
- Artistic creativity
- Stress resistance

### Step 5: Career Goals

**Priorities** (Rank top 3):
1. High income
2. Job stability
3. Interest alignment
4. Growth potential
5. Work-life balance
6. Social status
7. Freedom/Flexibility

**After Graduation Plan**:
- ① Work immediately
- ② Graduate school
- ③ Study abroad
- ④ Civil service exam
- ⑤ Undecided

**Target Career** (Optional)

### Step 6: Family Background

**Economic Status**:
- ① Difficult (needs loans/scholarships)
- ② Average
- ③ Middle class
- ④ Well-off
- ⑤ Wealthy

**Target Employment City**:
- ① Tier-1 cities (BJ/SH/GZ/SZ)
- ② New tier-1 (Hangzhou, Nanjing, etc.)
- ③ Provincial capital
- ④ Home province
- ⑤ No preference

**Family Industry Resources** (Optional)

### Step 7: Preferences

**School Priority**:
- ① Prestige first (985/211)
- ② Major first
- ③ Location first
- ④ Balanced

**Major Direction Preferences** (Multi-select):
- Engineering
- Science
- Medicine
- Business/Economics
- Humanities
- Arts
- Education
- Law/Politics

**Accept Adjustment**:
- ① Must accept
- ② Partially acceptable
- ③ Do not accept

## Parsing Logic

The system supports multiple input formats:

### Format 1: Numbered
```
1. 李明
2. 浙江
3. 612
4. 15230
5. R
6. 物理、数学
```

### Format 2: Compact
```
李明 浙江 612分 15230名 物化地 R 不接受社交
```

### Format 3: Natural Language
```
我叫李明，浙江考生，612分位次15230，
选了物理化学地理，属于动手型，不喜欢社交
```

## Output

Parsed data structure:
```json
{
  "basic_info": {
    "name": "李明",
    "province": "浙江"
  },
  "exam_info": {
    "score": 612,
    "rank": 15230,
    "subjects": ["物理", "化学", "地理"]
  },
  "interest_profile": {
    "holland_code": "RI",
    "primary_type": "现实型",
    "secondary_type": "研究型",
    "dislikes": ["社交应酬"]
  },
  "ability_assessment": {
    "strong": ["物理", "数学"],
    "weak": ["化学"]
  },
  "career_goals": {
    "plan": "本科就业",
    "priorities": ["收入高", "符合兴趣", "前景好"]
  },
  "family_background": {
    "economic": "中等",
    "target_city": "新一线城市"
  },
  "preferences": {
    "school_priority": "专业优先",
    "major_directions": ["工科类"],
    "adjustment": "可接受部分调剂"
  }
}
```

## Recommendation Based on Holland Codes

| Code | Name | Traits | Recommended Majors |
|------|------|--------|-------------------|
| **R** | Realistic | Hands-on, practical | CS, EE, Mechanical, Automation |
| **I** | Investigative | Analytical, research | Math, Physics, Medicine, Chemistry |
| **A** | Artistic | Creative, expressive | Design, Architecture, Media, Arts |
| **S** | Social | Helping, teaching | Education, Medicine, Psychology |
| **E** | Enterprising | Leading, managing | Business, Economics, Finance, Law |
| **C** | Conventional | Organized, structured | Accounting, Statistics, Finance |

## Best Practices

1. **Start with 3-minute version** for most consultations
2. **Use 1-minute version** only when time is extremely limited
3. **Switch to 7-step version** if more detailed planning is needed
4. **Always verify**: Score, Rank, and Holland type are mandatory
5. **Quality over speed**: Incomplete information leads to poor recommendations
