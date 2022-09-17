from http import HTTPStatus

from django.test import TestCase, Client

from ..models import Group, Post, User


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user1)
        cls.user2 = User.objects.create_user(username='author')
        cls.author = Client()
        cls.author.force_login(cls.user2)
        cls.group = Group.objects.create(
            title='Test_title',
            slug='Test_URL',
            description='Test_description',
        )
        cls.post = Post.objects.create(
            author=cls.user2,
            text='Test_text',
            group=cls.group,
        )

    def test_guest_client_access_to_pages(self):
        """Доступ для неавторизованного пользователя"""
        pages = ('/',
                 f'/group/{self.group.slug}/',
                 f'/profile/{self.user1.username}/',
                 f'/posts/{self.post.id}/')
        for page in pages:
            response = self.client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_id_edit_exists_at_desired_location(self):
        """Страница /posts/post_id/edit/ доступна автору."""
        response = self.author.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_id_edit_redirect_of_authorized_client(self):
        """
        Редирект авторизованного пользователя
        на страницу поста.
        """
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_create_post_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_exists_at_desired_location(self):
        """Страница /unexisting_page/ доступна любому пользователю."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """
        URL-адрес использует соответствующий шаблон.
        Вкл. проверка шаблона страницы 404 Not found.
        """
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user2.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.author.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_redirect_anonymous_on_admin_login(self):
        """
        Редирект неавторизованного пользователя при
        попытке создать, отредактировать пост
        создать комментарий к посту или
        подписаться на автора.
        """
        redir_1 = '/auth/login/?next=/create/'
        redir_2 = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        redir_3 = f'/auth/login/?next=/posts/{self.post.id}/comment/'
        redir_4 = f'/auth/login/?next=/profile/{self.user2.username}/follow/'

        urls = {
            '/create/': redir_1,
            f'/posts/{self.post.id}/edit/': redir_2,
            f'/posts/{self.post.id}/comment/': redir_3,
            f'/profile/{self.user2.username}/follow/': redir_4,
        }
        for url, redirect in urls.items():
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)
                self.assertRedirects(response, redirect)
