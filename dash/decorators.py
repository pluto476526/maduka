from django.shortcuts import redirect
from django.contrib import messages

def access_required(min_level):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                profile = getattr(request.user, 'profile', None)
                if profile and profile.access_level >= min_level:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, "You don't have permission to access the page.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        return _wrapped_view
    return decorator

