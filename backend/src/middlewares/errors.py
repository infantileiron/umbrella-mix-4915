import logging

from fastapi.responses import JSONResponse
from pymysql.err import OperationalError

logger = logging.getLogger(__name__)


def register(app):
    @app.exception_handler(OperationalError)
    def database_unavailable(request, exc):
        logger.error('Database unavailable for request %s: %s', request.state.request_id, exc.args[0])
        return JSONResponse({'detail': '数据库暂时不可用，请重试'}, status_code=503)
