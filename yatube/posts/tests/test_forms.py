import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='IvanIvanov')
        cls.another_user = User.objects.create_user(username='PetrPetrov')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_user = Client()
        self.post_author = Client()
        self.post_author.force_login(self.user_author)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.another_user)

    def test_authorized_user_create_post(self):
        """Проверка создания поста авторизованным клиентом."""
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Начинаю новую тетрадь дневника, послѣ почти мѣсячнаго...',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.post_author.post(
            reverse('posts:create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user_author.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user_author)
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(post.image.name, 'posts/small.gif')

    def test_post_author_edit_post(self):
        """Проверка редактирования поста его автором."""
        post = Post.objects.create(
            text='Какой-то текст, который мы вставим',
            author=self.user_author,
            group=self.group,
        )
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.id,
        }
        response = self.post_author.post(
            reverse(
                'posts:edit',
                args=[post.id]
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post.id}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.get(id=post.id)
        self.assertTrue(post.text == form_data['text'])
        self.assertTrue(post.author == self.user_author)
        self.assertTrue(post.group_id == form_data['group'])

    def test_nonauthorized_user_create_post(self):
        """Проверка создания поста не авторизованным пользователем."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
        }
        response = self.guest_user.post(
            reverse('posts:create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        redirect = reverse('login') + '?next=' + reverse('posts:create')
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_authorized_user_edit_post(self):
        """Проверка редактирования поста авторизованным пользователем."""
        post = Post.objects.create(
            text='Какой-то текст, который мы вставим',
            author=self.user_author,
            group=self.group,
        )
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.id,
        }
        response = self.authorized_user.post(
            reverse(
                'posts:edit',
                args=[post.id]
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post.id}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.get(id=post.id)
        self.assertNotEqual(post.text, form_data['text'])
        self.assertNotEqual(post.group, form_data['group'])

    def test_nonauthorized_user_create_post(self):
        """Проверка редактирования поста не авторизованным пользователем."""
        post = Post.objects.create(
            text='Какой-то текст, который мы вставим',
            author=self.user_author,
            group=self.group,
        )
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.id,
        }
        response = self.guest_user.post(
            reverse(
                'posts:edit',
                args=[post.id]
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        redirect = (
                reverse('users:login')
                + '?next=' + reverse('posts:edit', args=[post.id])
        )

        self.assertRedirects(response, redirect)
        self.assertNotEqual(post.text, form_data['text'])
        self.assertNotEqual(post.group, form_data['group'])

    def test_authorized_user_create_comment(self):
        """Проверка создания комментария авторизованным клиентом."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Какой-то текст, который мы вставим для проверки',
            author=self.user_author)
        form_data = {'text': 'Какой-то тестовый комментарий'}
        response = self.authorized_user.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)
        comment = Comment.objects.latest('id')
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.another_user)
        self.assertEqual(comment.post_id, post.id)
        self.assertRedirects(
            response, reverse('posts:post_detail', args={post.id}))

    def test_nonauthorized_user_create_comment(self):
        """Проверка создания комментария не авторизованным пользователем."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Какой-то текст, который мы вставим для проверки',
            author=self.user_author)
        form_data = {'text': 'Какой-то тестовый комментарий'}
        response = self.guest_user.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}
            ),
            data=form_data,
            follow=True
        )
        redirect = reverse('login') + '?next=' + reverse(
            'posts:add_comment', kwargs={'post_id': post.id})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(response, redirect)
