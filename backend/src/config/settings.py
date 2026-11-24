import os
from pathlib import Path

DB = dict(
    host=os.getenv('DB_HOST', 'db'),
    port=int(os.getenv('DB_PORT', '3306')),
    user=os.getenv('MYSQL_USER', 'umbrella'),
    password=os.getenv('MYSQL_PASSWORD', 'umbrella_dev_db'),
    database=os.getenv('MYSQL_DATABASE', 'umbrella'),
    charset='utf8mb4',
    connect_timeout=3,
    read_timeout=6,
    write_timeout=6,
)
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
JWT_SECRET = os.getenv('JWT_SECRET', 'umbrella-mix-local-demo-key-change-before-hosting')
EXPORT_DIR = Path(os.getenv('EXPORT_DIR', '/app/artifacts'))
