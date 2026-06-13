# 🔍 Deep Code Analysis Report

**Generated:** 2026-06-13T16:27:02.003950

**Path:** /home/long/project/gaokao-volunteer-system


## 📋 Executive Summary

- **Total Files:** 128
- **Total Lines:** 28,852
- **Architecture Style:** MVC
- **Entry Points:** 1
- **Data Models:** 147
- **Business Rules:** 239
- **External Dependencies:** 72


## 🏗️ Architecture

**Style:** MVC

**Layers/Modules:**

- `admin/`
- `data/`
- `scripts/`
- `tests/`
- `skills/`

## 🚀 Entry Points & Execution Flow


### main

- **Location:** `admin/app.py`
- **Parameters:** argv
- **Business Logic:** ❌ No
- **Calls:** ArgumentParser, add_argument, add_argument, add_argument, add_argument

## 📊 Data Models


### Core Entities


**UserOrderRecord** (`admin/users.py`)


**CaseRecord** (`data/cases/models.py`)


### DTOs/Value Objects

- **OrderSummaryResponse** - admin/routes/orders.py
- **OrderMutationResponse** - admin/routes/orders.py
- **CreateOrderRequest** - admin/routes/orders.py
- **UpdateOrderRequest** - admin/routes/orders.py
- **UserSummaryResponse** - admin/routes/users.py

## 📜 Business Rules


### Validation Rules (219)

**rule_1:** Validation in login

- Location: `locustfile.py:login`
- Priority: medium
- Condition: `if not token:
                resp.failure("login response missing access_token")
                se...`

**rule_2:** Validation in hash_password

- Location: `admin/password.py:hash_password`
- Priority: high
- Condition: `if not plain:
        raise ValueError("password cannot be empty")
    salt = secrets.token_bytes(_S...`

**rule_3:** Validation in verify_password

- Location: `admin/password.py:verify_password`
- Priority: high
- Condition: `if not plain or not stored or _STORED_SEPARATOR not in stored:
        return False
    salt_hex, ha...`

**rule_4:** Validation in authenticate

- Location: `admin/db.py:authenticate`
- Priority: medium
- Condition: `if result is None:
        return None
    user, password_hash = result
    if not user.is_active:
 ...`

**rule_5:** Validation in authenticate

- Location: `admin/db.py:authenticate`
- Priority: medium
- Condition: `if not user.is_active:
        return None
    if not verify_password(password, password_hash):
    ...`


### Constraint Rules (20)

**rule_11:** Business constraint in log_event

- Location: `admin/logging_utils.py:log_event`
- Priority: critical
- Condition: `if not event:
        raise ValueError("log_event: 'event' is required")

    safe_fields: Dict[str,...`

**rule_14:** Business constraint in log_event_exc

- Location: `admin/logging_utils.py:log_event_exc`
- Priority: critical
- Condition: `if not event:
        raise ValueError("log_event_exc: 'event' is required")
    safe_fields: Dict[s...`

**rule_36:** Business constraint in main

- Location: `scripts/check_coverage_gate.py:main`
- Priority: critical
- Condition: `if overall < OVERALL_MIN:
        failures.append(
            f"overall coverage {_format_percent(o...`

**rule_37:** Business constraint in main

- Location: `scripts/check_coverage_gate.py:main`
- Priority: critical
- Condition: `if core < CORE_MIN:
        failures.append(
            f"core coverage {_format_percent(core)} < r...`

**rule_70:** Business constraint in main

- Location: `skills/gaokao-audit/scripts/validate_template.py:main`
- Priority: critical
- Condition: `if needle not in text:
            print(f"FAIL: placeholder missing: {needle!r}")
            retur...`


## 🔗 External Dependencies


### Other Dependencies

- contextlib
- contextvars
- secrets
- checker_integration
- models
- io
- dataclasses
- unittest
- xml
- base64
- datetime
- weasyprint
- schema
- sys
- csv

## 💧 Data Flows

- **external** → **admin/password.py:verify_password**
  - Data: plain, stored
  - Trigger: function_call
- **external** → **admin/db.py:create**
  - Data: username, password, role
  - Trigger: function_call
- **external** → **admin/db.py:update_last_login**
  - Data: user_id
  - Trigger: function_call
- **external** → **admin/app.py:_validate_and_log_settings**
  - Data: settings
  - Trigger: function_call
- **external** → **admin/app.py:create_app**
  - Data: settings
  - Trigger: function_call
- **external** → **admin/stats.py:generate_day_series**
  - Data: db_path
  - Trigger: function_call
- **external** → **scripts/gaokao-quick-3min.py:generate_quick_summary**
  - Data: info
  - Trigger: function_call
- **external** → **scripts/gaokao-quick-3min.py:generate_quick_recommendation**
  - Data: info
  - Trigger: function_call
- **external** → **scripts/gaokao-visual-report-v2.py:generate_student_radar**
  - Data: student_profile
  - Trigger: function_call
- **external** → **scripts/gaokao-visual-report-v2.py:generate_school_comparison**
  - Data: volunteer_list
  - Trigger: function_call

## 🛤️ Key Execution Paths


### main

Entry point: admin/app.py

**Steps:**

1. `main`
2. `test_visual_report_usage_message`
3. `test_visual_report_demo_mode`
4. `test_visual_report_json_input`
5. `test_audit_cli_end_to_end_generates_pdf_and_report_content`
6. `test_audit_to_report_flow`
7. `test_traceability_display_flow`
8. `test_main_generates_pdf_and_prints_report_path`
... and 1 more

### main

Entry point: scripts/check_coverage_gate.py

**Steps:**

1. `main`
2. `test_visual_report_usage_message`
3. `test_visual_report_demo_mode`
4. `test_visual_report_json_input`
5. `test_audit_cli_end_to_end_generates_pdf_and_report_content`
6. `test_audit_to_report_flow`
7. `test_traceability_display_flow`
8. `test_main_generates_pdf_and_prints_report_path`
... and 1 more

### main

Entry point: scripts/gaokao-quick-3min.py

**Steps:**

1. `main`
2. `test_visual_report_usage_message`
3. `test_visual_report_demo_mode`
4. `test_visual_report_json_input`
5. `test_audit_cli_end_to_end_generates_pdf_and_report_content`
6. `test_audit_to_report_flow`
7. `test_traceability_display_flow`
8. `test_main_generates_pdf_and_prints_report_path`
... and 1 more

## 💡 Recommendations


### For Understanding This Codebase

1. Start with entry points listed above
2. Review core entities and their relationships
3. Trace execution paths for key features
4. Review business rules for domain logic
5. Check external dependencies for integration points


### For Code Quality

1. Add documentation to entry points
2. Document business rules explicitly
3. Create architecture decision records (ADRs)
4. Add data flow diagrams
