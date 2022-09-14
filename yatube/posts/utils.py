from django.core.paginator import Paginator

from .constants import POSTS_PER_PAGE


def pagination(request, post_list):
    """Функция-обработчик организации контента на странице."""
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)
