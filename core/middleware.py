"""
Performance monitoring middleware.
"""
import logging
import time

logger = logging.getLogger(__name__)


class PerformanceMonitorMiddleware:
    """Monitor API response times."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        if duration > 0.5:  # Log slow requests
            logger.warning(
                f"Slow request: {request.method} {request.path} - {duration:.2f}s"
            )
        
        response['X-Response-Time'] = f"{duration:.3f}s"
        return response
