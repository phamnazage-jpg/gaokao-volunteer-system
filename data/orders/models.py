"""订单数据模型 (T4.1)

Order dataclass 覆盖 TECH_ARCHITECTURE §3.4 所有字段；敏感字段按加密/明文分字段存储。
to_dict / from_dict 负责明文↔密文自动转换（DAO 层直接调用）。
"""

from __future__ import annotations

import json
import random
import string
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, List, Optional, Union

from .crypto import encrypt, decrypt, hash_for_index
from .masking import mask_sensitive_dict


# 解密策略:
# - True  : 完整明文(权限内接口使用,如后台人工核对)
# - False : 完全移除明文字段(对外公开统计/审计日志)
# - "mask": 部分遮罩(列表/详情默认,138****1234)
DecryptPolicy = Union[bool, str]


def utc_now_iso() -> str:
    """返回当前 UTC 时间的 ISO8601 字符串（秒精度）。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def generate_order_id() -> str:
    """生成订单号 GKO-YYYYMMDD-XXXX（4 位大写字母+数字）。"""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"GKO-{date_part}-{rand}"


@dataclass
class Order:
    """订单数据模型。

    加密约定：
    - customer_phone / candidate_id_card 在 from_dict 时加密，to_dict 时解密；
      数据库落盘只看到 _enc 后缀字段。
    - customer_phone_hash 仅用于去重查询（SHA-256 hex）。
    """

    id: str
    source: str  # 'xianyu'|'wechat'|'web'|'school'
    external_id: Optional[str] = None
    service_version: str = "basic"  # 'audit'|'basic'|'standard'|'premium'
    amount_cents: int = 0
    status: str = "pending"
    status_updated_at: Optional[str] = None

    # 客户（明文/加密分字段）
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None  # 明文（API 入口接收）
    customer_phone_hash: Optional[str] = None  # 自动派生
    customer_wechat: Optional[str] = None

    # 考生
    candidate_name: Optional[str] = None
    candidate_id_card: Optional[str] = None  # 明文（API 入口接收）
    candidate_province: Optional[str] = None
    candidate_score: Optional[int] = None
    candidate_rank: Optional[int] = None
    candidate_subjects: List[str] = field(default_factory=list)
    candidate_interests: Optional[str] = None
    candidate_strong_subjects: Optional[str] = None
    candidate_weak_subjects: Optional[str] = None
    candidate_family: Optional[str] = None

    # 服务
    assigned_consultant: Optional[str] = None
    plan_file: Optional[str] = None
    audit_report: Optional[str] = None
    pdf_path: Optional[str] = None

    # 时间戳
    created_at: Optional[str] = None
    paid_at: Optional[str] = None
    started_at: Optional[str] = None
    delivered_at: Optional[str] = None
    completed_at: Optional[str] = None

    # 元数据
    notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    upgrade_from: Optional[str] = None

    def __post_init__(self) -> None:
        """自动派生 hash 与时间戳。"""
        if self.customer_phone and not self.customer_phone_hash:
            self.customer_phone_hash = hash_for_index(self.customer_phone)
        if not self.created_at:
            self.created_at = utc_now_iso()
        if not self.status_updated_at:
            self.status_updated_at = self.created_at
        # tags/subjects 入库为 JSON 字符串
        if isinstance(self.tags, list):
            self._tags_json = json.dumps(self.tags, ensure_ascii=False)
        if isinstance(self.candidate_subjects, list):
            self._subjects_json = json.dumps(
                self.candidate_subjects, ensure_ascii=False
            )

    # 序列化到 DB（加密敏感字段）
    def to_db_row(self) -> dict[str, Any]:
        """返回可直接写入 orders 表的字典（敏感字段已加密）。"""
        data = asdict(self)
        # 移除明文敏感字段
        data.pop("customer_phone", None)
        data.pop("candidate_id_card", None)
        # 加密落盘字段
        if self.customer_phone:
            data["customer_phone_enc"] = encrypt(self.customer_phone)
        if self.candidate_id_card:
            data["candidate_id_card_enc"] = encrypt(self.candidate_id_card)
        # tags/subjects JSON 化
        data["tags"] = json.dumps(self.tags, ensure_ascii=False)
        data["candidate_subjects"] = json.dumps(
            self.candidate_subjects, ensure_ascii=False
        )
        return data

    # 从 DB 反序列化（解密敏感字段）
    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "Order":
        """从数据库行构造 Order，自动解密敏感字段。"""
        data = dict(row)
        if data.get("customer_phone_enc"):
            data["customer_phone"] = decrypt(data["customer_phone_enc"])
        else:
            data["customer_phone"] = None
        if data.get("candidate_id_card_enc"):
            data["candidate_id_card"] = decrypt(data["candidate_id_card_enc"])
        else:
            data["candidate_id_card"] = None
        # JSON 列表字段
        for key in ("tags", "candidate_subjects"):
            raw = data.get(key)
            if raw:
                try:
                    data[key] = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    data[key] = []
            else:
                data[key] = []
        # 移除 DB-only 加密字段
        data.pop("customer_phone_enc", None)
        data.pop("candidate_id_card_enc", None)
        return cls(**data)

    def to_dict(self, decrypt_sensitive: DecryptPolicy = "mask") -> dict[str, Any]:
        """导出为字典。

        decrypt_sensitive 取值:
        - True   : 敏感字段以明文返回(权限内 API,如后台人工核对)
        - False  : 完全移除明文字段(对外公开统计/审计日志,仅保留 hash)
        - "mask" : 部分遮罩(列表/详情默认,如 138****1234,推荐)

        当传入未知字符串时,回退为 "mask",保证前端拿到的是遮罩而非明文 — 默认安全。
        """
        data = asdict(self)
        if decrypt_sensitive is True:
            return data
        if decrypt_sensitive is False:
            data.pop("customer_phone", None)
            data.pop("candidate_id_card", None)
            return data
        # 默认 / "mask" / 其他字符串:走遮罩路径
        return mask_sensitive_dict(data)
