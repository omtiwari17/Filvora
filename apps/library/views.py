from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import LibraryItem
from apps.tmdb.client import TMDBClient

@login_required
def my_list(request):
    items = LibraryItem.objects.filter(user=request.user).order_by('-added_at')
    client = TMDBClient()
    
    saved_items = []
    for item in items:
        if item.media_type == 'movie':
            data = client.get_movie(item.tmdb_id)
            data['media_type'] = 'movie'
            saved_items.append(data)
        elif item.media_type == 'tv':
            data = client.get_tv(item.tmdb_id)
            data['media_type'] = 'tv'
            saved_items.append(data)
            
    return render(request, 'library/list.html', {'saved_items': saved_items})

@login_required
def toggle_item(request):
    if request.method == 'POST':
        tmdb_id = request.POST.get('tmdb_id')
        media_type = request.POST.get('media_type')
        
        if tmdb_id and media_type:
            item, created = LibraryItem.objects.get_or_create(
                user=request.user,
                tmdb_id=tmdb_id,
                media_type=media_type
            )
            if not created:
                item.delete()
                return HttpResponse(f"""<button hx-post="/library/toggle/" hx-vals='{{"tmdb_id": "{tmdb_id}", "media_type": "{media_type}"}}' hx-swap="outerHTML" class="bg-gray-500/50 text-white px-8 py-3 rounded font-bold text-lg flex items-center gap-2 hover:bg-gray-500/70 transition backdrop-blur-sm"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg> My List</button>""")
            return HttpResponse(f"""<button hx-post="/library/toggle/" hx-vals='{{"tmdb_id": "{tmdb_id}", "media_type": "{media_type}"}}' hx-swap="outerHTML" class="bg-brand-500 text-white px-8 py-3 rounded font-bold text-lg flex items-center gap-2 hover:bg-red-600 transition shadow-lg shadow-brand-500/30"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg> Saved</button>""")
            
    return HttpResponse("Invalid", status=400)
