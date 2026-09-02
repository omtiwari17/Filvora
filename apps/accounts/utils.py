from apps.accounts.models import UserProfile

def get_active_profile(request):
    """
    Returns the currently active UserProfile for the authenticated user.
    If no active profile ID is stored in session or profile no longer exists,
    resolves to the user's first profile (creating one if none exist).
    """
    if not request.user.is_authenticated:
        return None

    profile_id = request.session.get('active_profile_id')
    profile = None
    if profile_id:
        profile = UserProfile.objects.filter(id=profile_id, user=request.user).first()

    if not profile:
        profile = UserProfile.objects.filter(user=request.user).first()
        if not profile:
            profile = UserProfile.objects.create(
                user=request.user,
                name=request.user.username.capitalize(),
                avatar=f"https://ui-avatars.com/api/?name={request.user.username}&background=111827&color=fff&bold=true",
                is_kids=False
            )
        request.session['active_profile_id'] = profile.id

    return profile
