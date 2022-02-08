import shutil
import tempfile

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.urls import reverse
from django.conf import settings

from ..models import Follow, Group, Post

NUM_POSTS_TEST = settings.NUM_POSTS_PER_PAGE + 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='IvanIvanov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            text='Начинаю новую тетрадь дневника, послѣ почти мѣсячнаго...',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def post_context(self, context):
        with self.subTest(context=context):
            self.assertEqual(context.id, self.post.id)
            self.assertEqual(context.text, self.post.text)
            self.assertEqual(context.pub_date, self.post.pub_date)
            self.assertEqual(context.author, self.post.author)
            self.assertEqual(context.group.id, self.post.group.id)
            self.assertEqual(context.image, self.post.image)

    def test_forms_show_correct(self):
        """Валидация формы."""
        context = {
            reverse('posts:create'),
            reverse('posts:edit', kwargs={'post_id': self.post.id, }),
        }
        for page in context:
            with self.subTest(reverse_page=page):
                response = self.authorized_client.get(page)
                self.assertIsInstance(
                    response.context['form'].fields['text'],
                    forms.fields.CharField
                )
                self.assertIsInstance(
                    response.context['form'].fields['group'],
                    forms.fields.ChoiceField
                )
                self.assertIsInstance(
                    response.context['form'].fields['image'],
                    forms.fields.ImageField
                )

    def test_index_page_show_correct_context(self):
        """Валидация контекста шаблона index.html."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.post_context(response.context['page_obj'][0])

    def test_groups_page_show_correct_context(self):
        """Валидация контекста шаблона group_list.html."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            )
        )
        self.assertEqual(response.context['group'], self.group)
        self.post_context(response.context['page_obj'][0])

    def test_profile_page_show_correct_context(self):
        """Валидация контекста шаблона profile.html."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(response.context['author'], self.user)
        self.post_context(response.context['page_obj'][0])

    def test_detail_page_show_correct_context(self):
        """Валидация контекста шаблона post_detail.html."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.post_context(response.context['post'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='auth',
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        for i in range(NUM_POSTS_TEST):
            Post.objects.create(
                text=f'Пост #{i}',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.unauthorized_client = Client()

    def test_paginator_on_pages(self):
        """Валидация паджинатора."""
        posts_on_first_page = settings.NUM_POSTS_PER_PAGE
        posts_on_second_page = NUM_POSTS_TEST - settings.NUM_POSTS_PER_PAGE
        addresses = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for address in addresses:
            with self.subTest(address=address):
                self.assertEqual(
                    len(self.unauthorized_client.get(
                        address).context.get('page_obj')),
                    posts_on_first_page
                )
                self.assertEqual(
                    len(self.unauthorized_client.get(
                        address + '?page=2').context.get('page_obj')),
                    posts_on_second_page
                )


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_autor = User.objects.create(username='IvanIvanov')
        cls.post_follower = User.objects.create(username='PetrPetrov')
        cls.post = Post.objects.create(
            text='Тестовый текст проверяем подписку',
            author=cls.post_autor,
        )

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.post_follower)
        self.follower_client = Client()
        self.follower_client.force_login(self.post_autor)

    def test_subscribe(self):
        """Валидация подписки на пользователя."""
        follow_count = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post_follower}
            )
        )
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(follow.author_id, self.post_follower.id)
        self.assertEqual(follow.user_id, self.post_autor.id)

    def test_posts_subscribe(self):
        """Валидация записей у тех, кто подписан."""
        post = Post.objects.create(
            author=self.post_autor,
            text="Тестовый текст проверяем подписку"
        )
        Follow.objects.create(
            user=self.post_follower,
            author=self.post_autor
        )
        response = self.author_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_unsubscribe(self):
        """Валидация отписки от пользователя."""
        Follow.objects.create(
            user=self.post_autor,
            author=self.post_follower
        )
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.post_follower}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_posts_unsubscribe(self):
        """Валидация записей у тех, кто не подписан."""
        post = Post.objects.create(
            author=self.post_autor,
            text="Тестовый текст проверяем отписку"
        )
        response = self.author_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(post, response.context['page_obj'].object_list)
