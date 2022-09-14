from django.test import TestCase

from ..models import Group, Post, User
from ..constants import POST_START_WITH


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост о птичках',
        )

    def test_post_model_have_correct_object_name(self):
        """У модели Post корректно работает метод __str__."""
        self.assertEqual(
            self.post.text[:POST_START_WITH], str(self.post),
            'Метод __str__ в модели Post работает некорректно',
        )

    def test_group_model_have_correct_object_name(self):
        """У модели Group корректно работает метод __str__."""
        self.assertEqual(
            self.group.title, str(self.group),
            'Метод __str__ в модели Group работает некорректно',
        )

    def test_verbose_name(self):
        """Verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Содержание',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value,
                )

    def test_help_text(self):
        """Help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Введите текст поста',
            'author': 'Выберите автора',
            'group': 'Выберите группу',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value,
                )
