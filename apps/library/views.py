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
                return HttpResponse("Removed")
            return HttpResponse("Added")
            
    return HttpResponse("Invalid", status=400)
