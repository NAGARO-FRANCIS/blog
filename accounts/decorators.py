from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def verified_identity_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        profile = request.user.profile
        if not profile.can_reserve_or_message:
            messages.warning(request, profile.identity_interaction_block_reason)
            return redirect('accounts:verification_docs')
        return view_func(request, *args, **kwargs)

    return wrapped_view
