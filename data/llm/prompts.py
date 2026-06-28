"""志愿填报 LLM Prompt 模板。"""

from __future__ import annotations

import json
from typing import Any


def build_audit_prompt(
    *,
    province: str,
    score: int | None,
    rank: int | None,
    subjects: list[str],
    existing_plan: str,
    crowd_db_recs: list[dict[str, Any]] | None = None,
) -> tuple[str, str]:
    """构建志愿方案审核 prompt。

    Returns:
        (system_prompt, user_prompt)
    """
    system = (
        "你是一位资深高考志愿填报顾问，精通各省录取规则、院校层次和风险识别。"
        "你的任务是审核用户提供的现有志愿方案，识别踩线、扎堆、梯度失衡等风险，"
        "并给出具体可操作的改进建议。"
        "请用中文回答，输出 JSON 格式。"
    )

    context_parts = [
        f"考试省份：{province}",
        f"高考分数：{score or '未提供'}",
        f"全省位次：{rank or '未提供'}",
        f"选科组合：{'、'.join(subjects) if subjects else '未提供'}",
    ]

    if crowd_db_recs:
        top_schools = [
            f"{r.get('name', '?')} - {r.get('major', '?')}"
            for r in crowd_db_recs[:5]
            if isinstance(r, dict)
        ]
        if top_schools:
            context_parts.append(f"同分段热门院校：{'；'.join(top_schools)}")

    context = "\n".join(context_parts)

    user = f"""请审核以下志愿方案并给出风险评估。

## 考生基本信息
{context}

## ⚠️ 特殊批次/就业清晰路径（必须考虑）
在审核方案时，请特别关注考生是否考虑了以下 12 条低分捡漏、体制内兜底或就业清晰的升学路径。
如果考生分数偏低（接近本科线或低于一本线），而方案中没有包含任何特殊批次路径，请在 key_findings 中明确提示：

**体制内编制类：**
1. **公费农科生**（提前批/本科批）：学费全免+住宿全免+生活补贴，毕业直接事业编（乡镇农业农村局/农技站），服务5年。分数要求低（本科线附近），95%家长不知道。
2. **定向基层医疗**（提前批）：培养乡镇卫生院医生/全科医生，毕业直接进基层卫生院事业编。学费减免，服务6年。分数在本科线附近，农村户籍优先。
3. **公费消防/应急管理**（提前批）：中国消防救援学院等，正式行政编制，五险一金齐全。体测比警校宽松，允许矫正视力，比警校低50-120分。
4. **司法系统定向/社区矫正**（提前批/本科批）：基层司法所、社区矫正中心定向招录，正式编制。不用公安联考，不卡身高视力，比警校低80-130分。
5. **公费师范生**（提前批）：部属6所师范+省属师范，学费全免+住宿全免+生活补贴，毕业有编有岗，回生源省份任教6年。部属需一本以上，省属分数更低。
6. **定向培养军士（士官）**（专科提前批）：48所院校遍布全国，专科线即可（380-450分），毕业直接进入部队服役，军士待遇。入学即享军龄。

**国企央企就业类：**
7. **铁路定向公费生**（专科提前批/本科批）：各大铁路局定向培养，国企正式编制，包分配全国。专科200-350分、本科400-460分就能上岸。
8. **央企/国企订单班**（专科批/本科批）：邮政/电网/电信/交通/石油/民航等央企与高职院校合作订单培养，毕业即就业。石家庄邮电（邮政）、郑州电力（国网）、广州民航（南航）等，360-430分可报，部分订单班分数线超本科线。

**降分/专项类：**
9. **少数民族预科班**（本科批）：仅限少数民族考生，可降分20-80分录取进入中央民族大学/大连民族大学等。预科1年后转入正式本科，无定向约束。
10. **三大专项计划**（提前批/本科批）：国家专项（面向脱贫县）、地方专项（面向农村户籍）、高校专项（教育部直属高校），可降分进入985/211。需满足户籍+学籍要求。
11. **非西藏生源定向西藏**（本科批）：最低可降至调档线下40分录取，毕业须到西藏工作5年。适合愿意去西藏发展的低分考生。
12. **军校/警校**（提前批）：虽然竞争激烈，但对于高分考生仍是最稳定的体制内路径。需通过严格体检/政审/体测。
13. **强基计划**（提前批）：39所985院校面向基础学科拔尖学生单独招生，需参加校测（85%高考+15%校测）。适合一本线以上80-150分的高分考生。

## 现有方案说明
{existing_plan or "用户未提供具体方案内容"}

## 请输出
请以 JSON 格式输出审核结果，包含以下字段：
{{
  "risk_level": "low|medium|high",
  "risk_summary": "一句话风险总结",
  "key_findings": ["风险点1", "风险点2", ...],
  "suggestions": ["建议1", "建议2", ...],
  "special_program_recommendations": [
    {{
      "program": "公费农科生|定向基层医疗|公费消防|铁路定向|司法定向",
      "reason": "为什么推荐这条路径",
      "match_score": 0-100
    }}
  ],
  "cwb_suggestions": {{
    "rush": ["冲刺院校1 - 专业", ...],
    "stable": ["稳妥院校1 - 专业", ...],
    "safety": ["保底院校1 - 专业", ...]
  }}
}}

注意：
- risk_level 基于踩线风险、扎堆程度和梯度合理性综合判断
- key_findings 最多 5 条，每条不超过 50 字
- special_program_recommendations 只在考生分数适合时推荐，否则返回空数组
- cwb_suggestions 每档至少 2 个院校-专业组合
- 如果信息不足，在 key_findings 里说明需要补充什么"""

    return system, user


def build_cwb_prompt(
    *,
    province: str,
    score: int,
    rank: int | None,
    subjects: list[str],
    target_cities: list[str] | None = None,
    target_majors: list[str] | None = None,
    crowd_db_recs: list[dict[str, Any]] | None = None,
) -> tuple[str, str]:
    """构建冲稳保方案生成 prompt。"""
    system = (
        "你是一位资深高考志愿填报顾问。根据考生分数、位次和偏好，"
        "生成冲稳保三档院校-专业建议。"
        "请用中文回答，输出 JSON 格式。"
    )

    context_parts = [
        f"省份：{province}",
        f"分数：{score}",
        f"位次：{rank or '未提供'}",
        f"选科：{'、'.join(subjects) if subjects else '未提供'}",
    ]
    if target_cities:
        context_parts.append(f"目标城市：{'、'.join(target_cities)}")
    if target_majors:
        context_parts.append(f"目标专业：{'、'.join(target_majors)}")
    if crowd_db_recs:
        recs = [
            f"{r.get('name', '?')}({r.get('major', '?')})"
            for r in crowd_db_recs[:8]
            if isinstance(r, dict)
        ]
        if recs:
            context_parts.append(f"同分段参考：{'；'.join(recs)}")

    context = "\n".join(context_parts)

    user = f"""请为以下考生生成冲稳保三档建议。

## 考生信息
{context}

## 请输出 JSON：
{{
  "rush": [
    {{"school": "校名", "major": "专业", "reason": "推荐理由（简短）"}}
  ],
  "stable": [
    {{"school": "校名", "major": "专业", "reason": "推荐理由"}}
  ],
  "safety": [
    {{"school": "校名", "major": "专业", "reason": "推荐理由"}}
  ]
}}

要求：
- 每档至少 3 个院校-专业组合
- 冲刺档目标分数约 {score + 20} 分段
- 稳妥档围绕 {score} 分段
- 保底档约 {score - 20} 分段
- 院校名和专业名要真实存在
- 如果考生分数偏低，保底档应包含以下特殊批次路径之一：
  - 公费农科生（提前批，事业编）
  - 定向基层医疗（提前批，事业编）
  - 消防定向（提前批，行政编）
  - 铁路定向（专科提前批/本科批，国企编）
  - 司法定向（提前批/本科批，政法编）"""

    return system, user


def build_full_plan_prompt(
    *,
    province: str,
    score: int,
    rank: int | None,
    subjects: list[str],
    target_cities: list[str] | None = None,
    target_majors: list[str] | None = None,
    family_background: str | None = None,
    interest_assessment: str | None = None,
    existing_plan: str | None = None,
    crowd_db_recs: list[dict[str, Any]] | None = None,
) -> tuple[str, str]:
    """构建完整志愿方案生成 prompt。"""
    system = (
        "你是一位资深高考志愿填报顾问，擅长结合考生分数、位次、选科、"
        "偏好和家庭背景，生成完整、可执行的志愿方案。"
        "方案应包含冲稳保梯度、院校专业推荐和风险提示。"
        "请用中文回答，输出 JSON 格式。"
    )

    context_parts = [
        f"省份：{province}",
        f"分数：{score}",
        f"位次：{rank or '未提供'}",
        f"选科：{'、'.join(subjects) if subjects else '未提供'}",
    ]
    if target_cities:
        context_parts.append(f"目标城市：{'、'.join(target_cities)}")
    if target_majors:
        context_parts.append(f"目标专业：{'、'.join(target_majors)}")
    if family_background:
        context_parts.append(f"家庭背景：{family_background}")
    if interest_assessment:
        context_parts.append(f"兴趣测评：{interest_assessment}")
    if existing_plan:
        context_parts.append(f"已有方案：{existing_plan}")
    if crowd_db_recs:
        recs = [
            f"{r.get('name', '?')}({r.get('major', '?')})"
            for r in crowd_db_recs[:10]
            if isinstance(r, dict)
        ]
        if recs:
            context_parts.append(f"同分段参考：{'；'.join(recs)}")

    context = "\n".join(context_parts)

    user = f"""请为以下考生生成完整的志愿填报方案。

## 考生完整信息
{context}

## 请输出 JSON：
{{
  "overall_assessment": "总体评价（2-3句话）",
  "risk_level": "low|medium|high",
  "strategy": "核心策略说明",
  "volunteers": [
    {{
      "batch": "提前批|本科批|专科批",
      "tier": "冲|稳|保",
      "school": "校名",
      "major": "专业",
      "reason": "推荐理由",
      "risk_note": "风险提示（可空）"
    }}
  ],
  "warnings": ["注意事项1", "注意事项2"],
  "next_steps": ["建议后续动作1", "建议后续动作2"]
}}

要求：
- volunteers 至少 8 条，覆盖冲稳保三档
- 每条都有具体的院校名和专业名（真实存在）
- 按 tier 分组排序：先冲后稳再保
- warnings 至少 2 条"""

    return system, user
