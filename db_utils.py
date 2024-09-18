from functools import wraps
from sqlalchemy.exc import OperationalError
from time import sleep

def retry_on_exception(retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if attempt == retries - 1:
                        raise
                    sleep(delay)
        return wrapper
    return decorator
