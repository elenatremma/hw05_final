import shutil
import tempfile
import os

from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test user')
        cls.group = Group.objects.create(
            title='Test_group_title',
            slug='Test_URL',
            description='Test_description',
        )
        cls.group2 = Group.objects.create(
            title='Test_group2_title',
            slug='Test_URL2',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user2 = User.objects.create_user(username='author')
        self.author = Client()
        self.author.force_login(self.user2)

        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='image.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.uploaded2 = SimpleUploadedFile(
            name='image2.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.form_data = {
            'text': 'New_text',
            'group': self.group2.id,
            'image': self.uploaded2,
        }
        self.post = Post.objects.create(
            text='Test text',
            author=self.user2,
            group=self.group,
            image=self.uploaded,
        )
        self.uploaded.seek(0)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """
        Валидная форма создает новую запись в базе.
        Проверка всех параметров поста, вкл. изображение.
        """
        post_list = Post.objects.count()
        posts_old = list(Post.objects.values_list('id', flat=True))
        response = self.author.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user2.username}),
        )
        self.assertEqual(Post.objects.count(), post_list + 1)
        new_post = list(Post.objects.exclude(id__in=posts_old))
        self.assertEqual(new_post[0].text, self.form_data['text'])
        self.assertEqual(new_post[0].author, self.post.author)
        self.assertEqual(new_post[0].group.id, self.form_data['group'])
        self.assertEqual(os.path.basename(
            new_post[0].image.name), self.form_data['image'].name)

    def test_post_edit(self):
        """
        Проверка изменения cуществующего поста при отправке валидной формы.
        """
        response = self.author.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}),
            data=self.form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertNotEqual(self.post.text, self.form_data['text'])
        self.assertNotEqual(self.group.id, self.form_data['group'])
        self.assertNotEqual(self.post.image, self.form_data['image'])
        self.assertEqual(self.post.author, self.user2)

    def test_new_сomment_correct_appearance(self):
        """
        Созданный комментарий  отображается на
        странице поста.
        """
        comments_list = Comment.objects.count()
        form_data = {
            'text': 'New comment to add'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_list + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='New comment to add').exists()
        )

    def test_cache_index_page(self):
        """Посты на странице index кешируются."""
        response = self.client.get(reverse('posts:index'))
        form_data = {
            'text': 'Cache test text',
        }
        self.author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response = self.client.get(reverse('posts:index'))
        self.assertNotIn(form_data['text'], response.content.decode())
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertIn(form_data['text'], response.content.decode())
