from fastapi import FastAPI, HTTPException
from redis.exceptions import RedisError

from src.middlewares import errors
from src.middlewares.request_id import request_id
from src.middlewares.response_policy import response_policy
from src.models.db import transaction
from src.routes import plans, runs, session, tickets
from src.utils.queue import redis

app = FastAPI(title='补雨修伞 · 工时差额拆解', version='1.0.0')
app.middleware('http')(request_id)
app.middleware('http')(response_policy)
errors.register(app)
for module in (session, tickets, plans, runs):
    app.include_router(module.router)


@app.get('/health')
def health():
    with transaction() as cursor:
        cursor.execute('SELECT 1 FROM comparison_plans LIMIT 1')
    try:
        redis.ping()
    except RedisError as exc:
        raise HTTPException(503, 'Redis 暂时不可用') from exc
    return {'status': 'ok'}
