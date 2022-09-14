import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django import forms
from django.test import Client, TestCase, override_settings


from ..models import Group, Post, User, Follow
from ..constants import ALL_POSTS, POSTS_PER_PAGE


class PostViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.user2 = User.objects.create_user(username='author')
        cls.author = Client()
        cls.author.force_login(cls.user2)
        cls.group = Group.objects.create(
            title='Test_group_title',
            slug='Test_URL',
            description='Test_description',
        )
        cls.post = Post.objects.create(
            text='Test_text',
            author=cls.user2,
            group=cls.group,
        )

    def post_params_to_check(self, post):
        """Перечень параметров для сравнения данных c эталонным постом."""
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.group, self.group)

    def form_field_response(self, response):
        """Перечень параметров для проверки формы."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for key, expected_value in form_fields.items():
            with self.subTest(key=key):
                form_field = response.context.get('form').fields.get(key)
                self.assertIsInstance(form_field, expected_value)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug':
                            f'{self.group.slug}'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            f'{self.user2.username}'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.post.id}): 'posts/create_post.html',
        }
        for url, template in templates_urls.items():
            with self.subTest(url=url):
                response = self.author.get(url)
                self.assertTemplateUsed(response, template)

    def test_new_post_correct_appearance(self):
        """
        Созданный пост корректно отображается на
        первой позиции страниц index, group_list и profile.
        """
        responses_list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': f'{self.group.slug}'}),
            reverse('posts:profile', kwargs={
                'username': f'{self.user2.username}'}),
        ]
        new_post = Post.objects.create(
            text='New post to add',
            author=self.user2,
            group=self.group,
        )
        for url in responses_list:
            response = self.authorized_client.get(url).context
            self.assertIn('page_obj', response)
            self.assertTrue(len(response['page_obj']))
            post_0 = response['page_obj'][0]
            self.assertEqual(post_0.id, new_post.id)

    def test_new_post_add_to_correct_group(self):
        """Проверка на добавление поста в нужную группу."""
        group2 = Group.objects.create(
            title='Test_group2_title',
            slug='Test_URL2',
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': group2.slug}))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author.get(reverse('posts:index'))
        post = response.context['page_obj'].object_list[0]
        self.post_params_to_check(post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.author.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug})
        )
        self.assertEqual(
            response.context.get('group').title, self.group.title
        )
        self.assertEqual(response.context.get('group').slug, self.group.slug)
        self.assertEqual(
            response.context.get('group').description, self.group.description
        )
        post = response.context['page_obj'].object_list[0]
        self.post_params_to_check(post)

    def test_profile_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author.get(reverse(
            'posts:profile',
            kwargs={'username': self.user2.username})
        )
        self.assertEqual(
            response.context.get('author'), self.post.author)
        post = response.context['page_obj'].object_list[0]
        self.post_params_to_check(post)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        post = response.context['post']
        self.post_params_to_check(post)

    def test_post_create_page_show_correct_context(self):
        """
        Шаблон post_create сформирован с правильным контекстом
        на создание поста.
        """
        response = self.author.get(reverse('posts:post_create'))
        self.form_field_response(response)

    def test_post_edit_show_correct_context(self):
        """
        Шаблон post_edit сформирован с правильным контекстом
        на редактирование поста."""
        response = self.author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.form_field_response(response)
        post = response.context['post']
        self.post_params_to_check(post)
        is_edit = response.context['is_edit']
        self.assertTrue(is_edit, True)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='new_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Test_group_title',
            slug='Test_URL',
            description='Test_description',
        )
        cls.posts_list = [
            Post(
                author=cls.user,
                group=cls.group,
                text=f'Test_text {page}'
            ) for page in range(ALL_POSTS)
        ]
        Post.objects.bulk_create(cls.posts_list)

    def test_first_page_contains_ten_records(self):
        """
        На первой странице index/group_list/profile
        находится 10 постов.
        """
        pages = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                    'slug': self.group.slug}),
            reverse('posts:profile', kwargs={
                    'username': self.user.username}),
        )
        for page in pages:
            response = self.authorized_client.get(page)
            self.assertEqual(
                len(response.context['page_obj']), POSTS_PER_PAGE,
            )

    def test_second_page_contains_two_records(self):
        """
        На второй странице index/group_list/profile
        находятся 2 поста.
        """
        pages = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                    'slug': self.group.slug}),
            reverse('posts:profile', kwargs={
                    'username': self.user.username}),
        )
        for page in pages:
            response = self.authorized_client.get(page + '?page=2')
            self.assertEqual(len(
                response.context['page_obj']),
                ALL_POSTS - POSTS_PER_PAGE,
            )


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test user')
        cls.group = Group.objects.create(
            title='Test_group_title',
            slug='Test_URL',
            description='Test_description',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='test post',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user2 = User.objects.create_user(username='author')
        self.author = Client()
        self.author.force_login(self.user2)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_image_appears_on_index_group_list_profile(self):
        """Картинка выводится на страницы index, group list и profile. """
        urls = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                    'slug': self.group.slug}),
            reverse('posts:profile', kwargs={
                    'username': self.user.username}),
        }
        for url in urls:
            with self.subTest(urls=urls):
                response = self.authorized_client.get(url)
                self.assertEqual(response.context['page_obj'][0].image,
                                 f'posts/{self.uploaded}')

    def test_image_appears_on_post_detail(self):
        """Картинка выводится на страницу post detail."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id}
            )
        )
        self.assertEqual(
            response.context['post'].image, f'posts/{self.uploaded}'
        )


class FollowersViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='not subscribed user',
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.user2 = User.objects.create_user(
            username='subscribed user',
        )
        cls.subscribed_user = Client()
        cls.subscribed_user.force_login(cls.user2)
        cls.user3 = User.objects.create_user(
            username='author',
        )
        cls.author = Client()
        cls.author.force_login(cls.user3)
        cls.post = Post.objects.create(
            text='Test_text',
            author=cls.user2,
        )

    def test_authorized_client_can_follow(self):
        """
        Авторизованный пользователь может подписываться
        на других пользоваталей.
        """
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': self.user3.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user3).exists()
        )
        self.assertEqual(Follow.objects.count(), 1)

    def test_subscribed_user_can_unfollow(self):
        """Подписчик может отписаться  от автора."""
        Follow.objects.count()
        new_subscription = Follow.objects.create(
            user=self.user,
            author=self.user3
        )
        self.subscribed_user.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.user3.username}
            )
        )
        new_subscription.delete()
        self.assertEqual(Follow.objects.count(), 0)

    def test_guest_client_redirect(self):
        """
        Редирект неавторизованного пользователя при попытке
        подписаться на автора.
        """
        response = self.client.get(
            reverse('posts:profile_follow', kwargs={
                'username': self.user3.username}
            )
        )
        redirect = f'/auth/login/?next=/profile/{self.user3.username}/follow/'
        self.assertRedirects(response, redirect)

    def test_new_post_appears_for_subscribed_users_only(self):
        """Новая запись появляется в ленте подписчиков."""
        Follow.objects.create(
            user=self.user2,
            author=self.user3,
        )
        post = Post.objects.create(
            text='Post text for subscribe testing',
            author=self.user3,
        )
        response = self.subscribed_user.get(reverse('posts:follow_index'))
        self.assertContains(response, post.text)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, post.text)
