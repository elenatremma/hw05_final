from django.contrib import admin

from .models import Group, Post, Comment, Follow


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Класс для настройки отображения модели Post
    в админ-панели через декоратор.
    """

    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """
    Класс для настройки отображения модели Group
    в админ-панели через декоратор.
    """

    list_display = ('title', 'slug', 'description')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Класс для настройки отображения модели Comment
    в админ-панели через декоратор.
    """

    list_display = ('post', 'author', 'text', 'created')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """
    Класс для настройки отображения модели Follow
    в админ-панели через декоратор.
    """

    list_display = ('author', 'user')
