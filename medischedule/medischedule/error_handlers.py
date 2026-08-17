import logging
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages

logger = logging.getLogger(__name__)

class MedischeduleException(Exception):
    """Base exception for all application-level errors."""
    status_code = 400
    error_code = "BAD_REQUEST"

    def __init__(self, message, error_code=None, status_code=None):
        super().__init__(message)
        self.message = message
        if error_code:
            self.error_code = error_code
        if status_code:
            self.status_code = status_code


class NotFoundError(MedischeduleException):
    status_code = 404
    error_code = "NOT_FOUND"


class ValidationError(MedischeduleException):
    status_code = 400
    error_code = "VALIDATION_ERROR"


class PermissionDeniedError(MedischeduleException):
    status_code = 403
    error_code = "PERMISSION_DENIED"


class ConflictError(MedischeduleException):
    status_code = 409
    error_code = "CONFLICT"


class ErrorHandlingMiddleware:
    """
    Global middleware to catch MedischeduleException and format the response.
    Returns JSON for AJAX/API requests, and performs redirects with alerts for HTML browser requests.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, MedischeduleException):
            return None  # Let default Django exception handling handle it

        # Determine if the request is an AJAX/API request
        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            request.path.startswith('/schedules/ajax/') or
            'application/json' in request.headers.get('accept', '')
        )

        if is_ajax:
            return JsonResponse({
                'success': False,
                'error': {
                    'code': exception.error_code,
                    'message': exception.message
                }
            }, status=exception.status_code)

        # For browser requests, display message and redirect back to previous page or dashboard
        messages.error(request, exception.message)
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('dashboard_home')
