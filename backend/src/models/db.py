from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

from src.config.settings import DB


@contextmanager
def transaction():
    conn = pymysql.connect(**DB, cursorclass=DictCursor, init_command="SET time_zone = '+00:00'")
    try:
        with conn.cursor() as cursor:
            yield cursor
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
