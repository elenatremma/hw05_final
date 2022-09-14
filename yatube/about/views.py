from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Функция-обработчик статичной страницы об авторе."""

    template_name = 'about/about_author.html'


class AboutTechView(TemplateView):
    """Функция-обработчик статичной страницы о технологии."""

    template_name = 'about/about_tech.html'
