from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import UserProfile

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create default profile
            default_p = UserProfile.objects.create(
                user=user,
                name=user.username.capitalize(),
                avatar=f"https://ui-avatars.com/api/?name={user.username}&background=111827&color=fff&bold=true",
                is_kids=False
            )
            login(request, user)
            request.session['active_profile_id'] = default_p.id
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profiles_view(request):
    profiles = list(UserProfile.objects.filter(user=request.user))
    if not profiles:
        default_p = UserProfile.objects.create(
            user=request.user,
            name=request.user.username.capitalize(),
            avatar=f"https://ui-avatars.com/api/?name={request.user.username}&background=111827&color=fff&bold=true"
        )
        profiles = [default_p]

    active_profile_id = request.session.get('active_profile_id', profiles[0].id)
    return render(request, 'accounts/profiles.html', {
        'profiles': profiles,
        'active_profile_id': active_profile_id
    })

@login_required
def create_profile(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_kids = request.POST.get('is_kids') == 'on' or request.POST.get('is_kids') == 'true'
        avatar_color = "10b981" if is_kids else "e50914"
        if name:
            p = UserProfile.objects.create(
                user=request.user,
                name=name,
                avatar=f"https://ui-avatars.com/api/?name={name}&background={avatar_color}&color=fff&bold=true",
                is_kids=is_kids
            )
            request.session['active_profile_id'] = p.id
    return redirect('/accounts/profiles/')

@login_required
def switch_profile(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id, user=request.user)
    request.session['active_profile_id'] = profile.id
    return redirect('/')

@login_required
def update_profile(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id, user=request.user)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_kids = request.POST.get('is_kids') == 'on' or request.POST.get('is_kids') == 'true'
        avatar_color = request.POST.get('avatar_color', '').strip().lstrip('#')
        if not avatar_color:
            avatar_color = "10b981" if is_kids else "e50914"

        if name:
            profile.name = name
            profile.is_kids = is_kids
            profile.avatar = f"https://ui-avatars.com/api/?name={name}&background={avatar_color}&color=fff&bold=true"
            profile.save()

    return redirect('/accounts/profiles/')

@login_required
def delete_profile(request, profile_id):
    profile = get_object_or_404(UserProfile, id=profile_id, user=request.user)
    if request.method == 'POST':
        # Don't delete if only 1 profile exists
        if UserProfile.objects.filter(user=request.user).count() > 1:
            is_active = request.session.get('active_profile_id') == profile.id
            profile.delete()
            # Only reassign active profile if the deleted profile was currently active
            if is_active:
                remaining = UserProfile.objects.filter(user=request.user).first()
                if remaining:
                    request.session['active_profile_id'] = remaining.id
    return redirect('/accounts/profiles/')
