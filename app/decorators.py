from functools import wraps
from flask import abort
from flask_login import current_user


def permission_required(code: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if not current_user.has_permission(code):
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped_view
    return decorator


def roles_required(*role_names):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if not current_user.role or current_user.role.name not in role_names:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped_view
    return decorator
