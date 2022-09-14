from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model


from .models import Post, Group, Follow
from .forms import PostForm, CommentForm
from .utils import pagination


User = get_user_model()


def index(request):
    """Функция-обработчик главной страницы проекта."""
    template = 'posts/index.html'
    post_list = Post.objects.select_related('group', 'author')
    page_obj = pagination(request, post_list)
    context = {'page_obj': page_obj}

    return render(request, template, context)


def group_posts(request, slug):
    """Функция-обработчик страницы сообществ."""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('group', 'author')
    page_obj = pagination(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, template, context)


def profile(request, username):
    """Функция-обработчик персональной страницы автора."""
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    user = request.user
    post_list = author.posts.select_related('group', 'author')
    page_obj = pagination(request, post_list)
    following = user.is_authenticated and Follow.objects.filter(
        user=user, author=author
    ).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }

    return render(request, template, context)


def post_detail(request, post_id):
    """Функция-обработчик страницы для просмотра отдельного поста."""
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, template, context)


@login_required
def post_create(request):
    """Функция-обработчик создания нового поста."""
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect('posts:profile', username=post.author)

    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    """Функция-обработчик для редактирования поста."""
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:

        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None,
    )
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect('posts:post_detail', post_id)

    return render(request, template, {
        'post': post,
        'form': form,
        'is_edit': True,
    })


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """
    Функция-обработчик, которая выводит посты авторов,
    на которых подписан текущий пользователь.
    """
    template = 'posts/follow.html'
    posts_to_sign = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group')
    page_obj = pagination(request, posts_to_sign)
    context = {'page_obj': page_obj}

    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Функция-обработчик, позволяющая подписаться на автора."""
    author = get_object_or_404(User, username=username)
    subscription = Follow.objects.filter(user=request.user, author=author)
    if request.user == author or subscription.exists():
        return redirect('posts:profile', username=username)
    else:
        Follow.objects.create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Функция-обработчик, позволяющая отписаться от автора."""
    author = get_object_or_404(User, username=username)
    subscription = Follow.objects.filter(user=request.user, author=author)
    if subscription.exists():
        Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:index')
