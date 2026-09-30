from app.api.routes.auth import router as auth_router
from app.api.routes.centres import router as centres_router
from app.api.routes.tests import router as tests_router
from app.api.routes.centre_tests import router as centre_tests_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.payments import router as payments_router

__all__ = [
    "auth_router",
    "centres_router",
    "tests_router",
    "centre_tests_router",
    "bookings_router",
    "payments_router",
]
