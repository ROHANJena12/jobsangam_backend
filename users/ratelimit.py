from django_redis import get_redis_connection

# def check_and_increment_email_otp_quota(email: str, window_seconds: int = 900, max_requests: int = 3):
#     conn = get_redis_connection("default")
#     key = f"otp_rl:{email.lower()}"

#     # Atomically increment count + set expiry
#     pipe = conn.pipeline()
#     pipe.incr(key, 1)
#     pipe.expire(key, window_seconds)
#     count, _ = pipe.execute()

#     remaining = max_requests - count
#     ttl = conn.ttl(key)

#     if remaining < 0:
#         return False, 0, ttl
#     return True, remaining, ttl

def check_and_increment_email_otp_quota(email: str, window_seconds: int = 900, max_requests: int = 3):
    # 🚧 Rate limiting is DISABLED below for testing purposes
    return True, max_requests, window_seconds

    # Below is the original logic — left intact but bypassed for now
    conn = get_redis_connection("default")
    key = f"otp_rl:{email.lower()}"

    pipe = conn.pipeline()
    pipe.incr(key, 1)
    pipe.expire(key, window_seconds)
    count, _ = pipe.execute()

    remaining = max_requests - count
    ttl = conn.ttl(key)

    if remaining < 0:
        return False, 0, ttl
    return True, remaining, ttl

def increment_wrong_otp(email: str, window_seconds: int = 900, max_fails: int = 5):
    conn = get_redis_connection("default")
    key = f"otp_fail:{email.lower()}"

    pipe = conn.pipeline()
    pipe.incr(key, 1)
    pipe.expire(key, window_seconds)
    count, _ = pipe.execute()

    remaining = max_fails - count
    ttl = conn.ttl(key)

    return count, max(remaining, 0), ttl


def reset_wrong_otp(email: str):
    conn = get_redis_connection("default")
    conn.delete(f"otp_fail:{email.lower()}")
