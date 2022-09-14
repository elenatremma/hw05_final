from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Класс формы для создания нового поста."""

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')


class CommentForm(forms.ModelForm):
    """Класс формы для создания нового комментария."""
    class Meta:
        model = Comment
        fields = ['text']
