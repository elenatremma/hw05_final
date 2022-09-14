from django.contrib import admin

from .models import Group, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Класс для настройки отображения модели
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
    Класс для настройки отображения модели
    в админ-панели через декоратор.
    """

    list_display = ('title', 'slug', 'description')
