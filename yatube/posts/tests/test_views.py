import shutil
import tempfile

from django.core.cache import cache
from django.conf import settings
from django.test import Client, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.test import Client, TestCase, override_settings


from ..models import Group, Post, User, Follow, Comment
from ..constants import ALL_POSTS, POSTS_PER_PAGE
from ..forms import PostForm, CommentForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test user')
        cls.group = Group.objects.create(
            title='Test_group_title',
            slug='Test_URL',
            description='Test_description',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user2 = User.objects.create_user(
            username='author',
        )
        self.author = Client()
        self.author.force_login(self.user2)
        self.user3 = User.objects.create_user(
            username='subscribed_user',
        )
        self.subscribed_user = Client()
        self.subscribed_user.force_login(self.user3)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.post = Post.objects.create(
            text='test post',
            author=self.user2,
            group=self.group,
            image=self.uploaded,
        )
        self.new_comment = Comment.objects.create(
            post=self.post,
            author=self.user2,
            text="New comment to add"
        )
        cache.clear()

    def post_params_to_check(self, post):
        """Перечень параметров для сравнения данных c эталонным постом."""
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, self.post.image)

    def form_to_check(self, response):
        """Создание экземпляра формы для проверки ее работы."""
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertIsInstance(form, PostForm)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
            reverse('posts:follow_index'): 'posts/follow.html',
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
        """Проверка объекта group из контекста."""
        self.assertEqual(
            response.context.get('group').title, self.group.title
        )
        self.assertEqual(response.context.get('group').slug, self.group.slug)
        self.assertEqual(
            response.context.get('group').description, self.group.description
        )
        """Проверка объекта post из контекста."""
        post = response.context['page_obj'].object_list[0]
        self.post_params_to_check(post)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        new_subscription = Follow.objects.create(
            author=self.user2,
            user=self.user3,
        )
        response = self.author.get(reverse(
            'posts:profile',
            kwargs={'username': self.user2.username})
        )
        """Проверка объекта author из контекста."""
        self.assertEqual(
            response.context.get('author'), self.post.author)
        """Проверка объекта following из контекста."""
        user_status = [
            self.client,
            self.authorized_client,
            self.author,
        ]
        for user in user_status:
            if new_subscription.user == user:
                self.assertIsNone(response.context.get('following'))
        if new_subscription.user == self.subscribed_user:
            self.assertIsNotNone(response.context.get('following'))
        """Проверка объекта post из контекста."""
        post = response.context['page_obj'].object_list[0]
        self.post_params_to_check(post)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        """Проверка объекта post из контекста."""
        post = response.context['post']
        self.post_params_to_check(post)
        """Проверка объекта form из контекста."""
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertIsInstance(form, CommentForm)
        """Проверка объекта comments из контекста."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        all_comments = self.post.comments.all()
        self.assertQuerysetEqual(
            response.context.get('comments'),
            all_comments, transform=lambda x: x,
        )

    def test_post_create_page_show_correct_context(self):
        """
        Шаблон post_create сформирован с правильным контекстом
        на создание поста.
        """
        response = self.author.get(reverse('posts:post_create'))
        self.form_to_check(response)

    def test_post_edit_show_correct_context(self):
        """
        Шаблон post_edit сформирован с правильным контекстом
        на редактирование поста."""
        response = self.author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        """Проверка объекта post из контекста."""
        post = response.context['post']
        self.post_params_to_check(post)
        """Проверка объекта form из контекста."""
        self.form_to_check(response)
        """Проверка объекта is_edit из контекста."""
        is_edit = response.context['is_edit']
        self.assertTrue(is_edit, True)

    def test_cache_index_page(self):
        """Посты на странице index кешируются."""
        response = self.client.get(reverse('posts:index'))
        new_post = Post.objects.create(
            text='Cache test text',
            author=self.user2,
            group=self.group,
        )
        response = self.client.get(reverse('posts:index'))
        self.assertNotIn(new_post.text, response.content.decode())
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertIn(new_post.text, response.content.decode())

    def test_authorized_client_can_follow(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей.
        """
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user2).exists()
        )
        follows_count = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                'username': self.user2.username}
            )
        )
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user2).exists()
        )

    def test_subscribed_user_can_unfollow(self):
        """Подписчик может отписаться от автора."""
        follows_count = Follow.objects.count()
        Follow.objects.create(
            user=self.user3,
            author=self.user2
        )
        self.subscribed_user.post(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.user2.username}
            )
        )
        self.assertEqual(Follow.objects.count(), follows_count)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user2).exists()
        )

    def test_new_follow_appears_for_subscribed_users(self):
        """Новая запись появляется в ленте подписчиков."""
        new_post = Post.objects.create(
            text='Post text for subscribtion testing',
            author=self.user2,
        )
        Follow.objects.create(
            user=self.user3,
            author=self.user2,
        )
        response = self.subscribed_user.get(reverse('posts:follow_index'))
        self.assertContains(response, new_post.text)

    def test_new_follow_does_not_appear_for_authorized_clients(self):
        """Новая запись не появляется в ленте не подписанных пользователей."""
        new_post = Post.objects.create(
            text='Post text for subscribtion testing',
            author=self.user2,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, new_post.text)


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
