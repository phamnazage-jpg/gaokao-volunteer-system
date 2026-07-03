"""路由模块 (T6.1)."""

from admin.routes.auth import router as auth_router
from admin.routes.cases import admin_router as admin_cases_router
from admin.routes.cases import router as cases_router
from admin.routes.health import router as health_router
from admin.routes.meta import router as meta_router
from admin.routes.notifications import page_router as notifications_page_router
from admin.routes.notifications import router as notifications_router
from admin.routes.orders import admin_router as admin_orders_router
from admin.routes.orders import router as orders_router
from admin.routes.stats import admin_router as admin_stats_router
from admin.routes.stats import router as stats_router
from admin.routes.sprint3_api import router as sprint3_api_router
from admin.routes.ui import router as ui_router
from admin.routes.users import router as users_router
from admin.routes.web_public import router as web_public_router

__all__ = [
    "auth_router",
    "cases_router",
    "admin_cases_router",
    "health_router",
    "meta_router",
    "notifications_router",
    "notifications_page_router",
    "orders_router",
    "admin_orders_router",
    "stats_router",
    "admin_stats_router",
    "sprint3_api_router",
    "ui_router",
    "users_router",
    "web_public_router",
]
