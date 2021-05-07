from redis import Redis
import os


# Get Redis instance
redis = Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=os.environ.get('REDIS_PORT', 6379))

def get_queue_number(user_id):
    """decide apropriate queue number for the user_id """

    if not redis.exists(user_id):
        return 0
    user_history = int(redis.get(user_id))
    if user_history in range(1, 6):
        return 1
    elif user_history in range(6, 16):
        return 2
    elif user_history in range(16, 26):
        return 3
    elif user_history in range(26, 36):
        return 4
    else:
        return 5


def update_user_history(user_id, expire_seconds):
    """Update user requests number history on every task submission"""
    
    if not redis.exists(user_id):
        redis.set(user_id, 1, expire_seconds)
    else:
        redis.set(user_id, int(redis.get(user_id)) + 1, expire_seconds)