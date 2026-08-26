"""
自定义 Django 中间件：统计每个 HTTP 请求的处理耗时
  "apps.inventory.middleware.RequestTimingMiddleware"
"""
import logging
import time

logger = logging.getLogger(__name__)


class RequestTimingMiddleware:
    """统计每个请求耗时：响应头 + 控制台日志。"""

    # 客户端可在响应头中看到该字段，例如：X-Request-Duration-Ms: 3.99
    HEADER = "X-Request-Duration-Ms"

    def __init__(self, get_response):
        # Django 在启动时注入
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response[self.HEADER] = f"{duration_ms:.2f}"
        logger.info(
            "%s %s -> %s %.2fms",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response
