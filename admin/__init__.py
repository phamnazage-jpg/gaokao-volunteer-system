"""管理后台 (T6.1).

提供 FastAPI 应用工厂、JWT 鉴权、订单/用户/案例 API 骨架。
"""

from admin.app import create_app

__all__ = ["create_app"]
