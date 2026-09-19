from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from .models import LibraryItem, CustomCollection, CustomCollectionItem, SceneBookmark, FavoritePerson
from apps.tmdb.client import TMDBClient
from apps.accounts.utils import get_active_profile

@login_required
def my_list(request):
    profile = get_active_profile(request)
    items = LibraryItem.objects.filter(user=request.user, profile=profile).order_by('-added_at')
    custom_collections = CustomCollection.objects.filter(user=request.user, profile=profile).prefetch_related('items')
    bookmarks = SceneBookmark.objects.filter(user=request.user, profile=profile).order_by('-created_at')
    favorite_people = FavoritePerson.objects.filter(user=request.user, profile=profile).order_by('-added_at')
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
        'bookmarks': bookmarks,
        'favorite_people': favorite_people,
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


@csrf_exempt
def add_bookmark(request):
    """Save a scene timestamp bookmark with user note for active profile."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'Please sign in to save scene bookmarks to your profile.'
        }, status=401)

    try:
        import json
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        tmdb_id = int(data.get('tmdb_id'))
        media_type = data.get('media_type', 'movie')
        title = data.get('title', '').strip() or ('Movie' if media_type == 'movie' else 'Series')
        raw_s = data.get('season')
        raw_e = data.get('episode')
        season = int(raw_s) if raw_s not in (None, '', 'null') else None
        episode = int(raw_e) if raw_e not in (None, '', 'null') else None
        pos_sec = float(data.get('position', 0))
        note = data.get('note', '').strip()
        poster_path = data.get('poster_path', '').strip()

        profile = get_active_profile(request)

        bookmark = SceneBookmark.objects.create(
            user=request.user,
            profile=profile,
            tmdb_id=tmdb_id,
            media_type=media_type,
            title=title,
            season=season,
            episode=episode,
            position_seconds=pos_sec,
            note=note,
            poster_path=poster_path
        )

        return JsonResponse({
            'status': 'success',
            'id': bookmark.id,
            'title': bookmark.title,
            'timestamp': bookmark.formatted_timestamp,
            'seconds': bookmark.position_seconds,
            'note': bookmark.note,
            'play_url': bookmark.play_url
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
def delete_bookmark(request, bookmark_id):
    """Deletes a scene bookmark scoped to active user profile."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

    profile = get_active_profile(request)
    bookmark = get_object_or_404(SceneBookmark, id=bookmark_id, user=request.user, profile=profile)
    bookmark.delete()
    if request.headers.get('HX-Request'):
        return HttpResponse("")
    return JsonResponse({'status': 'success'})


@csrf_exempt
@login_required
def toggle_collection_library(request):
    """Batch toggle all movies in a franchise collection in/out of active profile's library."""
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    try:
        if request.content_type == 'application/json':
            import json
            data = json.loads(request.body)
        else:
            data = request.POST

        collection_id = int(data.get('collection_id', 0))
        movie_ids_raw = data.get('movie_ids', '')
        movie_ids = [int(x.strip()) for x in str(movie_ids_raw).split(',') if x.strip().isdigit()]

        profile = get_active_profile(request)
        if not movie_ids and collection_id:
            from apps.tmdb.client import TMDBClient
            coll_data = TMDBClient().get_collection(collection_id)
            if coll_data and 'parts' in coll_data:
                movie_ids = [p['id'] for p in coll_data['parts']]

        if not movie_ids:
            return JsonResponse({'status': 'error', 'message': 'No movie IDs provided'}, status=400)

        existing = LibraryItem.objects.filter(
            user=request.user,
            profile=profile,
            tmdb_id__in=movie_ids,
            media_type='movie'
        )
        existing_ids = set(existing.values_list('tmdb_id', flat=True))

        # If all are already in library, remove them all
        if len(existing_ids) >= len(movie_ids):
            existing.delete()
            is_all_saved = False
        else:
            for mid in movie_ids:
                LibraryItem.objects.get_or_create(
                    user=request.user,
                    profile=profile,
                    tmdb_id=mid,
                    media_type='movie'
                )
            is_all_saved = True

        if request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            from django.http import HttpResponse

            from apps.watch.models import WatchProgress, UserRating
            watched_count = WatchProgress.objects.filter(
                user=request.user, profile=profile, tmdb_id__in=movie_ids, media_type='movie', completed=True
            ).count()
            ratings = list(UserRating.objects.filter(
                user=request.user, profile=profile, tmdb_id__in=movie_ids, media_type='movie'
            ).values_list('score', flat=True))
            avg_score = int(round(sum(ratings) / len(ratings))) if ratings else 0

            html = render_to_string('components/collection_actions_bar.html', {
                'collection': {
                    'id': collection_id,
                    'parts': [{'id': mid} for mid in movie_ids],
                    'watched_count': watched_count,
                    'total_count': len(movie_ids),
                    'is_all_watched': watched_count == len(movie_ids),
                    'completion_percent': int((watched_count / len(movie_ids)) * 100) if movie_ids else 0,
                    'is_all_saved': is_all_saved,
                    'collection_score': avg_score,
                    'movie_ids_str': ','.join(str(x) for x in movie_ids),
                },
                'movie_ids_str': ','.join(str(x) for x in movie_ids),
                'is_all_saved': is_all_saved,
            }, request=request)
            resp = HttpResponse(html)
            import json
            resp['HX-Trigger'] = json.dumps({
                'sagaLibraryChanged': {
                    'collection_id': collection_id,
                    'is_all_saved': is_all_saved,
                    'movie_ids': movie_ids
                }
            })
            return resp

        return JsonResponse({'status': 'ok', 'is_all_saved': is_all_saved})
    except (ValueError, TypeError, KeyError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
def toggle_favorite_person(request):
    """Toggle an actor/director in or out of the active profile's favorites."""
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    if not request.user.is_authenticated:
        if request.headers.get('HX-Request'):
            resp = HttpResponse("Please sign in", status=401)
            resp['HX-Redirect'] = '/accounts/login/?next=' + request.META.get('HTTP_REFERER', '/')
            return resp
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

    try:
        import json
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        person_id = int(data.get('person_id', 0))
        name = str(data.get('name', '')).strip()
        profile_path = str(data.get('profile_path', '')).strip()
        known_for_department = str(data.get('known_for_department', '')).strip() or 'Acting'

        if not person_id:
            return JsonResponse({'status': 'error', 'message': 'person_id is required'}, status=400)

        profile = get_active_profile(request)

        # If name is missing, attempt to fetch from TMDB
        if not name:
            client = TMDBClient()
            p_data = client.get_person(person_id)
            if p_data:
                name = p_data.get('name', f'Person {person_id}')
                if not profile_path:
                    profile_path = p_data.get('profile_path') or ''
                if known_for_department == 'Acting' and p_data.get('known_for_department'):
                    known_for_department = p_data.get('known_for_department')

        fav = FavoritePerson.objects.filter(user=request.user, profile=profile, person_id=person_id).first()
        if fav:
            fav.delete()
            is_favorite = False
        else:
            FavoritePerson.objects.create(
                user=request.user,
                profile=profile,
                person_id=person_id,
                name=name or f"Artist {person_id}",
                profile_path=profile_path,
                known_for_department=known_for_department
            )
            is_favorite = True

        if request.headers.get('HX-Request'):
            from django.template.loader import render_to_string
            html = render_to_string('components/person_favorite_button.html', {
                'person': {
                    'id': person_id,
                    'name': name,
                    'profile_path': profile_path,
                    'known_for_department': known_for_department
                },
                'is_favorite': is_favorite
            }, request=request)
            resp = HttpResponse(html)
            resp['HX-Trigger'] = json.dumps({
                'favoritePersonChanged': {
                    'person_id': person_id,
                    'is_favorite': is_favorite,
                    'name': name
                }
            })
            return resp

        return JsonResponse({'status': 'ok', 'is_favorite': is_favorite, 'person_id': person_id})
    except (ValueError, TypeError, KeyError) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
def delete_favorite_person(request, person_id):
    """Deletes a favorite person record scoped to the active profile."""
    if request.method != 'POST':
        return HttpResponseBadRequest("POST required")

    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

    profile = get_active_profile(request)
    FavoritePerson.objects.filter(user=request.user, profile=profile, person_id=person_id).delete()
    if request.headers.get('HX-Request'):
        return HttpResponse("")
    return JsonResponse({'status': 'success', 'person_id': person_id})
