# 提前批/定向/专项计划规则补充方案

**编写日期**: 2026-06-27  
**目标**: 在现有系统基础上，系统性地补齐提前批、定向培养、专项计划等特殊招生类型的规则和数据

---

## 一、当前真实状态诊断

### 1.1 crowd_db program_type 覆盖

| 类型           | 覆盖省数 | 状态        |
| -------------- | -------- | ----------- |
| 师范教育类     | 31       | ✅ 充分     |
| 医学类特色     | 30       | ✅ 充分     |
| 艺体类         | 26       | ✅ 基本充分 |
| 农林类特色     | 24       | ✅ 基本充分 |
| 国际涉外导向   | 16       | ⚠️ 中等     |
| 师范院校特色类 | 11       | ⚠️ 中等     |
| 民族类特色     | 10       | ⚠️ 中等     |
| 农林院校特色类 | 6        | ❌ 不足     |
| 医学院校特色类 | 6        | ❌ 不足     |
| 公安院校       | 3        | ❌ 严重不足 |
| 军校           | 1        | ❌ 严重不足 |

### 1.2 special_programs.json 已有项目

| program_type       | 名称                   | 状态 |
| ------------------ | ---------------------- | ---- |
| rural_medical      | 农村订单定向免费医学生 | ✅   |
| public_agriculture | 公费农科生             | ✅   |
| fire_rescue        | 公费消防/应急管理定向  | ✅   |
| railway_directed   | 铁路定向公费生         | ✅   |
| judicial_directed  | 司法系统定向生         | ✅   |

### 1.3 special_programs_rules.json 已有规则

9条全国级规则，覆盖：提前批概念/户籍要求/服务年限/体测/分数门槛/免学费/免联考

### 1.4 完全缺失的类型

| 缺失类型                 | 影响面            | 优先级 |
| ------------------------ | ----------------- | ------ |
| 军校（31省仅1省有）      | 3万+考生/年       | P0     |
| 公安/警校（31省仅3省有） | 2万+考生/年       | P0     |
| 国家专项计划             | 农村/贫困地区考生 | P0     |
| 地方专项计划             | 农村/贫困地区考生 | P0     |
| 高校专项计划             | 农村/贫困地区考生 | P1     |
| 公费师范生               | 师范类考生        | P1     |
| 免费医学定向             | 医学类考生        | P1     |
| 航海类提前批             | 航海类考生        | P2     |
| 中外合作办学             | 高分段考生        | P2     |
| 民族班/预科              | 少数民族考生      | P2     |
| 体育类单招               | 体育特长生        | P2     |
| 艺术类校考               | 艺术特长生        | P2     |

---

## 二、补充方案

### Phase 1: P0 类型补充（军校 + 公安 + 专项计划）

#### 1.1 special_programs.json 新增项目

```json
[
  {
    "program_type": "military_academy",
    "program_name": "军校提前批",
    "batch": "本科提前批",
    "description": "军队院校招收普通高中毕业生，入学即入伍，享受军人待遇，毕业后分配工作",
    "score_requirement": "一本线以上20-50分（各省不同）",
    "special_requirements": [
      "年龄不超过20周岁（截止当年8月31日）",
      "未婚",
      "参加政治考核（政审）",
      "参加军检（体格检查+心理检测）",
      "视力：裸眼≥4.5（部分专业≥4.8）",
      "身高：男≥162cm，女≥160cm",
      "体重：标准体重±25%"
    ],
    "career_prospect": "毕业后授中尉军衔，分配至部队工作",
    "score_advantage": "比同层次普通院校低30-80分",
    "provinces": "全国31省"
  },
  {
    "program_type": "police_academy",
    "program_name": "公安院校提前批",
    "batch": "本科提前批",
    "description": "公安院校公安专业招生，需参加公安联考，入警率90%+",
    "score_requirement": "一本线附近（部分省二本线以上）",
    "special_requirements": [
      "年龄不超过22周岁",
      "未婚",
      "参加政治考察",
      "参加体检（视力裸眼≥4.8，色觉正常）",
      "参加体能测试（50米跑/立定跳远/1000米跑/引体向上）",
      "身高：男≥170cm，女≥160cm",
      "参加面试"
    ],
    "career_prospect": "毕业后参加公安联考，入警率90%+，正式编制",
    "score_advantage": "比同层次普通院校低20-60分",
    "provinces": "全国31省"
  },
  {
    "program_type": "national_special_plan",
    "program_name": "国家专项计划",
    "batch": "本科批（单设志愿）",
    "description": "面向脱贫县（原贫困县）农村考生的专项招生计划，由中央部门高校和各省一本院校承担",
    "score_requirement": "一本线以上（通常低于普通批10-30分）",
    "special_requirements": [
      "具有实施区域当地连续3年以上户籍",
      "具有户籍所在县高中连续3年学籍并实际就读",
      "父母或法定监护人具有当地户籍"
    ],
    "career_prospect": "与普通批相同专业相同待遇",
    "score_advantage": "比普通批同校同专业低10-30分",
    "provinces": "全国（832个脱贫县）"
  },
  {
    "program_type": "local_special_plan",
    "program_name": "地方专项计划",
    "batch": "本科批（单设志愿）",
    "description": "各省属一本院校面向本省农村考生的专项招生计划",
    "score_requirement": "一本线以上（通常低于普通批15-40分）",
    "special_requirements": [
      "具有实施区域农村户籍",
      "具有户籍所在县高中连续3年学籍并实际就读"
    ],
    "career_prospect": "与普通批相同专业相同待遇",
    "score_advantage": "比普通批同校同专业低15-40分",
    "provinces": "各省自定实施区域"
  },
  {
    "program_type": "university_special_plan",
    "program_name": "高校专项计划",
    "batch": "本科提前批/本科批",
    "description": "教育部直属高校和其他自主招生高校面向农村考生的专项计划（如"自强计划""筑梦计划"等）",
    "score_requirement": "一本线以上（各校自定）",
    "special_requirements": [
      "考生及其父母或法定监护人户籍地在实施区域的农村",
      "考生具有当地连续3年以上户籍",
      "考生具有户籍所在县高中连续3年学籍并实际就读",
      "部分高校需要单独报名/面试/笔试"
    ],
    "career_prospect": "与普通批相同专业相同待遇",
    "score_advantage": "通常降分20-60分",
    "provinces": "全国（95所高校）"
  }
]
```

#### 1.2 special_programs_rules.json 新增规则

```json
[
  {
    "rule_id": "special.military.age_limit",
    "title": "军校年龄限制",
    "description": "报考军队院校的考生年龄不超过20周岁（截止当年8月31日），且必须未婚",
    "provinces": "全国",
    "program_type": "military_academy",
    "category": "提前批-军校"
  },
  {
    "rule_id": "special.military.physical_exam",
    "title": "军校军检要求",
    "description": "军队院校招生须参加军检，包括体格检查和心理检测。视力要求裸眼≥4.5（部分专业≥4.8），身高男≥162cm女≥160cm",
    "provinces": "全国",
    "program_type": "military_academy",
    "category": "提前批-军校"
  },
  {
    "rule_id": "special.police.physical_test",
    "title": "公安院校体能测试",
    "description": "公安院校招生须参加体能测试，包括50米跑、立定跳远、1000米跑（男）/800米跑（女）、引体向上（男）/仰卧起坐（女）",
    "provinces": "全国",
    "program_type": "police_academy",
    "category": "提前批-公安"
  },
  {
    "rule_id": "special.police.entry_exam",
    "title": "公安联考入警率",
    "description": "公安院校公安专业毕业生参加全国公安机关人民警察考试（公安联考），入警率90%+，非公安专业不能参加",
    "provinces": "全国",
    "program_type": "police_academy",
    "category": "提前批-公安"
  },
  {
    "rule_id": "special.national_plan.eligibility",
    "title": "国家专项计划报考资格",
    "description": "国家专项计划要求考生具有实施区域当地连续3年以上户籍+户籍所在县高中连续3年学籍并实际就读+父母或法定监护人具有当地户籍",
    "provinces": "全国（832个脱贫县）",
    "program_type": "national_special_plan",
    "category": "专项计划"
  },
  {
    "rule_id": "special.local_plan.eligibility",
    "title": "地方专项计划报考资格",
    "description": "地方专项计划要求考生具有实施区域农村户籍+户籍所在县高中连续3年学籍并实际就读。各省自定具体实施区域",
    "provinces": "各省自定",
    "program_type": "local_special_plan",
    "category": "专项计划"
  },
  {
    "rule_id": "special.university_plan.eligibility",
    "title": "高校专项计划报考资格",
    "description": "高校专项计划要求考生及父母户籍地在实施区域农村+当地连续3年以上户籍+户籍所在县高中连续3年学籍并实际就读+部分高校需单独报名",
    "provinces": "全国",
    "program_type": "university_special_plan",
    "category": "专项计划"
  },
  {
    "rule_id": "special.special_plan.score_advantage",
    "title": "三大专项计划分数优势",
    "description": "国家专项通常降10-30分，地方专项通常降15-40分，高校专项通常降20-60分。具体降分幅度因省份和学校而异",
    "provinces": "全国",
    "program_type": null,
    "category": "专项计划"
  }
]
```

#### 1.3 crowd_db 31省JSON 新增 program_type 标记

在31个省的 crowd_db JSON 中，对 score_ranges 的 recommendations 选择性新增以下 program_type：

| 新增 program_type | 标记范围                                        | 标记数量预估 |
| ----------------- | ----------------------------------------------- | ------------ |
| 军校              | 600+分段院校中有军校（国防科大/陆军工程大学等） | 每省2-5条    |
| 公安/警校         | 500+分段院校中有公安院校（中国人民公安大学等）  | 每省3-6条    |
| 专项计划          | 各分段均可标注（专项计划覆盖面广）              | 每省5-10条   |
| 公费师范          | 500+分段师范院校                                | 每省2-4条    |
| 中外合作办学      | 550+分段                                        | 每省3-8条    |
| 民族班/预科       | 民族类院校                                      | 每省1-3条    |
| 航海类            | 450+分段                                        | 每省1-2条    |

---

### Phase 2: P1 类型补充（公费师范 + 免费医学 + 更多细节）

#### 2.1 special_programs.json 新增

```json
[
  {
    "program_type": "public_normal_university",
    "program_name": "公费师范生（部属/省属）",
    "batch": "本科提前批",
    "description": "教育部直属师范大学（北师大/华东师大/华中师大/陕师大/东北师大/西南大学）和省属师范大学公费师范生。免学费+住宿费+生活补贴，毕业包分配，需服务6年",
    "score_requirement": "部属一本线以上30-80分，省属一本线附近",
    "special_requirements": [
      "毕业后回生源所在省份任教不少于6年",
      "部属公费师范生可免试在职攻读教育硕士",
      "省属公费师范生毕业回到定向县任教"
    ],
    "career_prospect": "毕业包分配，有编有岗",
    "score_advantage": "与普通批同校持平或略低",
    "provinces": "全国"
  },
  {
    "program_type": "free_medical_oriented",
    "program_name": "免费医学定向（本科）",
    "batch": "本科提前批/本科批",
    "description": "中西部省份定向培养全科医生，免学费+住宿费+生活补贴，毕业回基层卫生院工作6年",
    "score_requirement": "一本线附近或二本线以上",
    "special_requirements": [
      "毕业后回定向县基层医疗卫生机构服务6年",
      "农村户籍优先",
      "部分地区要求签订定向培养协议"
    ],
    "career_prospect": "毕业直接进基层卫生院事业编",
    "score_advantage": "通常降20-50分",
    "provinces": "中西部省份（约22省）"
  }
]
```

#### 2.2 special_programs_rules.json 新增规则

- 公费师范服务年限
- 公费师范编制保障
- 免费医学定向服务年限
- 免费医学定向编制保障
- 中外合作办学学费标准
- 民族预科班就读年限（预科1年+本科4年）

---

### Phase 3: P2 类型补充（航海/中外合作/民族预科/体育/艺术）

#### 3.1 special_programs.json 新增

- 航海类提前批（大连海事/武汉理工等）
- 中外合作办学（各高校国际学院）
- 民族班/预科（民族院校/普通院校民族班）
- 体育类单独招生
- 艺术类校考（独立艺术院校）

#### 3.2 规则补充

- 航海类体检要求（视力/色觉/身高）
- 中外合作办学学费范围（3-10万/年）
- 民族预科班录取分数线（降80分）
- 体育单招文化课分数线
- 艺术类省考vs校考区别

---

## 三、实施文件清单

| 文件                                           | 改动内容                                 | Phase     |
| ---------------------------------------------- | ---------------------------------------- | --------- |
| `data/crowd_db/special_programs.json`          | 新增10个特殊批次项目                     | Phase 1-3 |
| `data/rules/special_programs_rules.json`       | 新增15-20条规则                          | Phase 1-3 |
| `data/crowd_db/*.json` (31个省)                | 新增 program_type 标记到 recommendations | Phase 1-2 |
| `data/crowd_db/special_programs_loader.py`     | 扩展查询接口（按批次/按类型筛选）        | Phase 1   |
| `admin/routes/web_public.py`                   | 政策中心页增加"提前批与专项计划"板块     | Phase 1   |
| `data/crowd_db/tests/test_special_programs.py` | 新增专项计划/军校/公安匹配测试           | Phase 1   |
| `data/crowd_db/tests/test_program_type.py`     | 新增类型断言                             | Phase 1   |

---

## 四、验证标准

### Phase 1 验收标准

- [ ] special_programs.json 有10个项目（原5+新5）
- [ ] special_programs_rules.json 有17+条规则（原9+新8）
- [ ] 军校 program_type 覆盖从1省提升到至少20省
- [ ] 公安 program_type 覆盖从3省提升到至少15省
- [ ] 政策中心页有"提前批与专项计划"入口
- [ ] 测试全部通过

### Phase 2 验收标准

- [ ] special_programs.json 有12个项目（10+2）
- [ ] 公费师范 program_type 覆盖至少20省
- [ ] 免费医学定向 program_type 覆盖至少15省
- [ ] 测试全部通过

### Phase 3 验收标准

- [ ] special_programs.json 有15个项目（12+3-5）
- [ ] 中外合作办学/民族预科/航海类均有标记
- [ ] 测试全部通过

---

## 五、实施路线图

| 阶段    | 工作量                               | 优先级 | 预估时间 |
| ------- | ------------------------------------ | ------ | -------- |
| Phase 1 | special_programs+rules+31省标记+前端 | P0     | 2-3天    |
| Phase 2 | 公费师范+免费医学+规则补充           | P1     | 1-2天    |
| Phase 3 | 航海/中外/民族/体育/艺术             | P2     | 1-2天    |

**总计**: 4-7天

---

## 六、数据来源

所有新增数据应基于以下来源，不做推测：

1. 教育部"阳光高考"平台（gaokao.chsi.com.cn）
2. 各省教育考试院官方文件
3. 军队院校招生简章
4. 公安院校招生简章
5. 各高校专项计划招生简章

**原则**: 每条规则和每个项目描述都必须可在上述来源中找到依据，不编造具体分数/日期/政策细节。
