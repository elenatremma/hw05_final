from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    """Добавление фильтра с перечнем HTML-атрибутов."""

    return field.as_widget(attrs={'class': css})
