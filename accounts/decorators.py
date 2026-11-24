from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse

def mongo_login_required(view_func):
    """
    Decorator requiring an authenticated Mongo user session.
    Redirects unauthenticated users to the appropriate login portal:
    - Citizen paths redirect to Public Citizen Login (/auth/citizen/login/)
    - Authority paths redirect to Authority Sign In (/auth/login/)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not getattr(request, 'mongo_user', None):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                return JsonResponse({'status': 'error', 'message': 'Authentication required. Please log in.'}, status=401)
            is_citizen_path = '/public' in request.path or '/assistant' in request.path
            if is_citizen_path:
                messages.warning(request, "Please sign in or register with your Citizen account to access the Public Portal.")
                return redirect(f"/auth/citizen/login/?next={request.path}")
            else:
                messages.warning(request, "Authentication required. Please sign in to access the Control Room.")
                return redirect(f"/auth/login/?next={request.path}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def role_required(allowed_roles):
    """
    Decorator requiring specific role(s) e.g. ['Traffic Authority'].
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = getattr(request, 'mongo_user', None)
            if not user:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                    return JsonResponse({'status': 'error', 'message': 'Authentication required.'}, status=401)
                is_citizen_path = '/public' in request.path or '/assistant' in request.path
                if is_citizen_path:
                    messages.warning(request, "Please sign in to continue.")
                    return redirect(f"/auth/citizen/login/?next={request.path}")
                else:
                    messages.warning(request, "Please sign in with your officer credentials to continue.")
                    return redirect(f"/auth/login/?next={request.path}")

            user_role = user.get('role', 'Public User')
            if user_role not in allowed_roles:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                    return JsonResponse({'status': 'error', 'message': 'Access forbidden: Insufficient security privileges.'}, status=403)
                messages.error(request, "Access restricted. You do not have permission to view private traffic authority data.")
                return redirect('public:dashboard')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
