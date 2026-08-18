"""Expose the request user to model-layer helpers (audit trail)."""
import threading

_state = threading.local()


def get_current_user():
    return getattr(_state, "user", None)


def get_current_request():
    return getattr(_state, "request", None)


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _state.request = request
        _state.user = getattr(request, "user", None)
        try:
            return self.get_response(request)
        finally:
            _state.user = None
            _state.request = None
