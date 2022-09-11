import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='admin')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='img1.gif',
            content=cls.image,
            content_type='image/gif'
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Созданный тестовый пост',
            'group': self.group.pk,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        reversed_redirect = reverse(
            'posts:profile', args=(self.user.username,)
        )
        COUNT_OFFSET = 1
        test_post = Post.objects.first()
        self.assertRedirects(response, reversed_redirect)
        self.assertEqual(Post.objects.count(), post_count + COUNT_OFFSET)
        self.assertEqual(test_post.text, form_data['text'])
        self.assertEqual(test_post.group.pk, form_data['group'])
        self.assertEqual(test_post.image, f"posts/{form_data['image']}")

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group,
            image=self.uploaded,
        )
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text=post.text,
                group=self.group,
                image=post.image
            ).exists()
        )
        new_image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='img2.gif',
            content=new_image,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Отредактированный тестовый пост',
            'group': self.group.pk,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(post.pk,)),
            data=form_data,
            follow=True,
        )
        reversed_redirect = reverse('posts:post_detail', args=(post.pk,))
        self.assertRedirects(response, reversed_redirect)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.image, f"posts/{form_data['image']}")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CommentsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='admin')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form = CommentForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """
        Валидная форма создания комментария.
        Только авторизованный пользователь может оставить комментарий.
        Проверка авторизованного пользователя.
        """
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.pk,)),
            data=form_data,
            follow=True,
        )
        reversed_redirect = reverse(
            'posts:post_detail', args=(self.post.pk,)
        )
        COUNT_OFFSET = 1
        self.assertRedirects(response, reversed_redirect)
        self.assertEqual(
            Comment.objects.count(),
            comments_count + COUNT_OFFSET,
        )
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data['text'])

    def test_guest_cant_commenting(self):
        """
        Валидная форма создания комментария.
        Только авторизованный пользователь может оставить комментарий.
        Проверка неавторизованного пользователя.
        """
        comments_count = Comment.objects.count()
        form_data = {
            'post': self.post.pk,
            'author': self.guest_client,
            'text': 'Тестовый комментарий',
        }
        self.guest_client.post(
            reverse('posts:add_comment', args=(self.post.pk,)),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count)
