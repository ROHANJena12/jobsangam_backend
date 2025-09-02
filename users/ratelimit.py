# from django_redis import get_redis_connection

# # def check_and_increment_email_otp_quota(email: str, window_seconds: int = 900, max_requests: int = 3):
# #     conn = get_redis_connection("default")
# #     key = f"otp_rl:{email.lower()}"

# #     # Atomically increment count + set expiry
# #     pipe = conn.pipeline()
# #     pipe.incr(key, 1)
# #     pipe.expire(key, window_seconds)
# #     count, _ = pipe.execute()

# #     remaining = max_requests - count
# #     ttl = conn.ttl(key)

# #     if remaining < 0:
# #         return False, 0, ttl
# #     return True, remaining, ttl

# def check_and_increment_email_otp_quota(email: str, window_seconds: int = 900, max_requests: int = 3):
#     # 🚧 Rate limiting is DISABLED below for testing purposes
#     return True, max_requests, window_seconds

#     # Below is the original logic — left intact but bypassed for now
#     conn = get_redis_connection("default")
#     key = f"otp_rl:{email.lower()}"

#     pipe = conn.pipeline()
#     pipe.incr(key, 1)
#     pipe.expire(key, window_seconds)
#     count, _ = pipe.execute()

#     remaining = max_requests - count
#     ttl = conn.ttl(key)

#     if remaining < 0:
#         return False, 0, ttl
#     return True, remaining, ttl

# def increment_wrong_otp(email: str, window_seconds: int = 900, max_fails: int = 5):
#     conn = get_redis_connection("default")
#     key = f"otp_fail:{email.lower()}"

#     pipe = conn.pipeline()
#     pipe.incr(key, 1)
#     pipe.expire(key, window_seconds)
#     count, _ = pipe.execute()

#     remaining = max_fails - count
#     ttl = conn.ttl(key)

#     return count, max(remaining, 0), ttl


# def reset_wrong_otp(email: str):
#     conn = get_redis_connection("default")
#     conn.delete(f"otp_fail:{email.lower()}")

from django_redis import get_redis_connection
from django.conf import settings
import time

# Keys
def k_block(email): return f"otp:block:{email.lower()}"
def k_send_count(email): return f"otp:send_count:{email.lower()}"
def k_last_sent(email): return f"otp:last_sent:{email.lower()}"
def k_fail_count(email): return f"otp:fail_count:{email.lower()}"

def _ttl(conn, key):
    ttl = conn.ttl(key)
    return ttl if ttl and ttl > 0 else 0

# --- Blocking ---
def is_blocked(email: str):
    conn = get_redis_connection("default")
    return conn.exists(k_block(email))

def block_user(email: str, block_seconds: int = None):
    conn = get_redis_connection("default")
    block_for = block_seconds or getattr(settings, "OTP_BLOCK_SECONDS", 7200)
    conn.setex(k_block(email), block_for, 1)

def get_block_ttl(email: str):
    conn = get_redis_connection("default")
    return _ttl(conn, k_block(email))

# --- Send quota ---
def check_and_increment_email_otp_quota(email: str):
    """
    Enforces:
      - 2 min cooldown between sends
      - Max 3 sends per 2h window
    Returns (allowed: bool, reason: str|None, ttl: int)
    """
    conn = get_redis_connection("default")

    # Cooldown check
    last_sent_key = k_last_sent(email)
    cooldown = getattr(settings, "OTP_RESEND_COOLDOWN_SECONDS", 120)
    if conn.exists(last_sent_key):
        return False, "cooldown", _ttl(conn, last_sent_key)

    # Windowed send limit
    send_key = k_send_count(email)
    window = getattr(settings, "OTP_SEND_WINDOW_SECONDS", 7200)
    max_sends = getattr(settings, "OTP_MAX_SENDS_PER_WINDOW", 3)

    pipe = conn.pipeline()
    pipe.incr(send_key, 1)
    pipe.expire(send_key, window)
    count, _ = pipe.execute()

    if count > max_sends:
        return False, "window_limit", _ttl(conn, send_key)

    # Mark cooldown
    conn.setex(last_sent_key, cooldown, int(time.time()))
    return True, None, 0

# --- Wrong OTP attempts ---
def increment_wrong_otp(email: str, window_seconds: int = 7200, max_fails: int = 3):
    """
    Count OTP verification failures.
    After max_fails, caller should block_user().
    Returns (count, remaining, ttl)
    """
    conn = get_redis_connection("default")
    key = k_fail_count(email)

    pipe = conn.pipeline()
    pipe.incr(key, 1)
    pipe.expire(key, window_seconds)
    count, _ = pipe.execute()

    remaining = max_fails - count
    ttl = _ttl(conn, key)

    return count, max(remaining, 0), ttl

def reset_wrong_otp(email: str):
    conn = get_redis_connection("default")
    conn.delete(k_fail_count(email))
