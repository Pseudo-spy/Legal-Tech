"""API dependencies — exports authentication and database session getters."""

from ..db.session import get_async_session
from ..core.security import get_current_user_id

get_db = get_async_session
get_current_user = get_current_user_id