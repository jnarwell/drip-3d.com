"""Rate limiting configuration using slowapi."""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter - uses IP address as key
# Can be extended to use user ID for authenticated endpoints
limiter = Limiter(key_func=get_remote_address)
