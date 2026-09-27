from django.contrib import admin
from .models import (
    LibraryItem,
    CustomCollection,
    CustomCollectionItem,
    SceneBookmark,
    FavoritePerson,
)


@admin.register(LibraryItem)
class LibraryItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile', 'tmdb_id', 'media_type', 'added_at')
    list_filter = ('media_type', 'added_at')
    search_fields = ('user__username', 'profile__name', 'tmdb_id')
    ordering = ('-added_at',)
    readonly_fields = ('added_at',)


class CustomCollectionItemInline(admin.TabularInline):
    model = CustomCollectionItem
    extra = 1


@admin.register(CustomCollection)
class CustomCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'profile', 'items_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'user__username', 'profile__name', 'description')
    ordering = ('-created_at',)
    inlines = [CustomCollectionItemInline]
    readonly_fields = ('created_at',)

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Total Items'


@admin.register(CustomCollectionItem)
class CustomCollectionItemAdmin(admin.ModelAdmin):
    list_display = ('collection', 'tmdb_id', 'media_type', 'added_at')
    list_filter = ('media_type', 'added_at')
    search_fields = ('collection__name', 'tmdb_id')
    ordering = ('-added_at',)
    readonly_fields = ('added_at',)


@admin.register(SceneBookmark)
class SceneBookmarkAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'profile', 'media_type', 'tmdb_id', 'formatted_timestamp', 'created_at')
    list_filter = ('media_type', 'created_at')
    search_fields = ('title', 'note', 'user__username', 'tmdb_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'formatted_timestamp')


@admin.register(FavoritePerson)
class FavoritePersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'known_for_department', 'person_id', 'user', 'profile', 'added_at')
    list_filter = ('known_for_department', 'added_at')
    search_fields = ('name', 'user__username', 'person_id')
    ordering = ('-added_at',)
    readonly_fields = ('added_at',)
