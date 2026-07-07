# LLM_DOMAIN_DATA_COVERAGE_2026-07-07

## Scope

Validates that LLM prompt special-program promises have backing structured data and rules.

## Current required program keywords

- 公费农科生
- 定向基层医疗
- 公费消防
- 司法系统定向
- 公费师范生
- 定向培养军士
- 铁路定向
- 央企/国企订单班
- 少数民族预科班
- 三大专项计划
- 非西藏生源定向西藏
- 军校/警校
- 强基计划

## Synonym mapping

- 定向基层医疗 ↔ 农村订单定向免费医学生 / 免费医学定向 / `rural_medical`
- 订单班 ↔ 央企/国企订单班 / `enterprise_order`
- 军校/警校 ↔ `police_military`

The coverage gate accepts these synonym mappings because the prompt uses user-facing labels while data files use official/programmatic names.

