from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import LibraryItem, CustomCollection, CustomCollectionItem
from apps.tmdb.client import TMDBClient
from apps.accounts.utils import get_active_profile

@login_required
def my_list(request):
    profile = get_active_profile(request)
    items = LibraryItem.objects.filter(user=request.user, profile=profile).order_by('-added_at')
    custom_collections = CustomCollection.objects.filter(user=request.user, profile=profile).prefetch_related('items')
    client = TMDBClient()
    
    from apps.watch.models import UserRating
    user_ratings = {
        (r.tmdb_id, r.media_type): r.score
        for r in UserRating.objects.filter(user=request.user, profile=profile)
    }

    saved_items = []
    for item in items:
        if item.media_type == 'movie':
            data = client.get_movie(item.tmdb_id)
            data['media_type'] = 'movie'
            data['display_title'] = data.get('title', '')
            data['rating_score'] = user_ratings.get((item.tmdb_id, 'movie'), 0)
            saved_items.append(data)
        elif item.media_type == 'tv':
            data = client.get_tv(item.tmdb_id)
            data['media_type'] = 'tv'
            data['display_title'] = data.get('name', '')
            data['rating_score'] = user_ratings.get((item.tmdb_id, 'tv'), 0)
            saved_items.append(data)
            
    return render(request, 'library/list.html', {
        'saved_items': saved_items,
        'custom_collections': custom_collections,
        'star_range': [1, 2, 3, 4, 5],
    })

@login_required
def create_collection(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        profile = get_active_profile(request)
        if name:
            CustomCollection.objects.create(user=request.user, profile=profile, name=name, description=description)
    return redirect('/library/')

@login_required
def delete_collection(request, collection_id):
    profile = get_active_profile(request)
    collection = get_object_or_404(CustomCollection, id=collection_id, user=request.user, profile=profile)
    if request.method == 'POST':
        collection.delete()
    return redirect('/library/')

@login_required
def toggle_item(request):
    if request.method == 'POST':
        tmdb_id = request.POST.get('tmdb_id')
        media_type = request.POST.get('media_type')
        variant = request.POST.get('variant', 'hero')
        
        if tmdb_id and media_type:
            profile = get_active_profile(request)
            item, created = LibraryItem.objects.get_or_create(
                user=request.user,
                profile=profile,
                tmdb_id=int(tmdb_id),
                media_type=media_type
            )
            if not created:
                item.delete()
                is_saved = False
            else:
                is_saved = True

            if variant == 'card':
                if is_saved:
                    return HttpResponse(f"""<button hx-post="/library/toggle/" hx-vals='{{"tmdb_id": "{tmdb_id}", "media_type": "{media_type}", "variant": "card"}}' hx-swap="outerHTML" onclick="event.preventDefault(); event.stopPropagation();" title="In My List" class="w-8 h-8 rounded-full bg-brand-500 hover:bg-red-600 text-white flex items-center justify-center shadow-lg transition-transform transform hover:scale-110"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" /></svg></button>""")
                else:
                    return HttpResponse(f"""<button hx-post="/library/toggle/" hx-vals='{{"tmdb_id": "{tmdb_id}", "media_type": "{media_type}", "variant": "card"}}' hx-swap="outerHTML" onclick="event.preventDefault(); event.stopPropagation();" title="Add to My List" class="w-8 h-8 rounded-full bg-gray-900/80 hover:bg-gray-800 text-white border border-gray-600/80 flex items-center justify-center shadow-lg transition-transform transform hover:scale-110"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" /></svg></button>""")

            # Default Hero / Detail variant
            if is_saved:
                return HttpResponse(f"""<button hx-post="/library/toggle/" hx-vals='{{"tmdb_id": "{tmdb_id}", "media_type": "{media_type}"}}' hx-swap="outerHTML" class="bg-brand-500 text-white px-8 py-3 rounded font-bold text-lg flex items-center gap-2 hover:bg-red-600 transition shadow-lg shadow-brand-500/30"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg> Saved</button>""")
            else:
                return HttpResponse(f"""<button hx-post="/library/toggle/" hx-vals='{{"tmdb_id": "{tmdb_id}", "media_type": "{media_type}"}}' hx-swap="outerHTML" class="bg-gray-500/50 text-white px-8 py-3 rounded font-bold text-lg flex items-center gap-2 hover:bg-gray-500/70 transition backdrop-blur-sm"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg> My List</button>""")
            
    return HttpResponse("Invalid", status=400)


