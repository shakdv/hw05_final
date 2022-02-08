from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )

        cls.user_author = User.objects.create_user(username='IvanIvanov')
        cls.another_user = User.objects.create_user(username='PetrPetrov')

        cls.post = Post.objects.create(
            text='Начинаю новую тетрадь дневника, послѣ почти мѣсячнаго...',
            author=cls.user_author,
            group=cls.group,
        )

    def setUp(self):
        self.unauthorized_user = Client()
        self.post_author = Client()
        self.post_author.force_login(self.user_author)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.another_user)
        cache.clear()

    def test_unauthorized_user_urls_status_code(self):
        """Проверка доступности страниц для неавторизованного пользователя."""
        status = HTTPStatus.OK
        url_status_code = {
            '/': status,
            f'/group/{self.group.slug}/': status,
            f'/profile/{self.user_author.username}/': status,
            f'/posts/{self.post.id}/': status,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }

        for url, response_code in url_status_code.items():
            with self.subTest(url=url):
                status_code = self.unauthorized_user.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_create_url_exists_at_desired_location(self):
        """Проверка доступности /create/ для авторизованного пользователя."""
        response = self.authorized_user.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location_authorized(self):
        """Проверка доступности страниц, /edit/ для авторизованного автора."""
        response = self.post_author.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(
                'posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user_author}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse(
                'posts:edit',
                kwargs={'post_id': self.post.id}): 'posts/create_post.html',
            reverse(
                'posts:create'): 'posts/create_post.html',
        }
        for address, template in templates_pages_names.items():
            with self.subTest(adress=address):
                response = self.post_author.get(address)
                self.assertTemplateUsed(response, template)
