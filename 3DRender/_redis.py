import redis

# decode_responses=True
redis_conn = redis.Redis(host='127.0.0.1', port=6379,
                         db=9,
                         max_connections=10)

if __name__ == '__main__':
    redis_conn.hset("test", "tttt", 1)
    print(type(redis_conn.hget("test", "tttt")))
