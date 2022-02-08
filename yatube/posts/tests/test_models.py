from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Начинаю новую тетрадь дневника, послѣ почти мѣсячнаго..',
        )

    def test_post_have_correct_object_name(self):
        """Проверяем, что у модели post корректно работает __str__."""
        self.assertEqual(
            self.post.text[:15],
            str(self.post),
            'Метод __str__ работает неправильно.'
        )

    def test_post_verbose_name(self):
        """Проверка verbose_name у post."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }

        for field, expected_value in field_verboses.items():
            with self.subTest(value=field):
                verbose_name = self.post._meta.get_field(field).verbose_name
                self.assertEqual(
                    verbose_name,
                    expected_value,
                    'Неправильное значение verbose_name у post'
                )

    def test_post_help_text(self):
        """Проверка help_text у post."""
        feild_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу', }

        for field, expected_value in feild_help_texts.items():
            with self.subTest(value=field):
                help_text = self.post._meta.get_field(field).help_text
                self.assertEqual(
                    help_text,
                    expected_value,
                    'Неправильное значение help_text у post'
                )


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_group_have_correct_object_name(self):
        """Проверяем, что у модели group корректно работает __str__."""
        self.assertEqual(
            self.group.title,
            str(self.group),
            'Метод __str__ работает неправильно.'
        )

    def test_post_verbose_name(self):
        """Проверка verbose_name у group."""
        field_verboses = {
            'title': 'Заголовок',
            'slug': 'ЧПУ',
            'description': 'Описание',
        }

        for field, expected_value in field_verboses.items():
            with self.subTest(value=field):
                verbose_name = self.group._meta.get_field(field).verbose_name
                self.assertEqual(
                    verbose_name,
                    expected_value,
                    'Неправильное значение verbose_name у group'
                )
