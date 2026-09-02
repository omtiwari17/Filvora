from .utils import get_active_profile

def active_profile_context(request):
    if request.user.is_authenticated:
        profile = get_active_profile(request)
        return {
            'active_profile': profile
        }
    return {
        'active_profile': None
    }
