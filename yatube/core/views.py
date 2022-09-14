from django.shortcuts import render


def page_not_found(request, exception):
    """Функция для обработки пользовательской страницы 404."""
    return render(
        request, 'core/404.html', {'path': request.path}, status=404
    )


def csrf_failure(request, reason=''):
    """Функция для обработки ошибки проверки CSRF."""
    return render(request, 'core/403.html')


def internal_server_error(request):
    """Функция для обработки пользовательской страницы 500."""
    return render(
        request, 'core/500.html', {'path': request.path}, status=500
    )
