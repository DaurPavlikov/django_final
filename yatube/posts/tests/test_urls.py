from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='admin')
        cls.not_author = User.objects.create_user(username='buster')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        cls.authorized_url_status = [
            '/',
            '/group/test-slug/',
            f'/profile/{cls.user.username}/',
            f'/posts/{cls.post.pk}/',
            '/create/',
            '/follow/',
        ]
        cls.user_correct_community_redirect = {
            f'/posts/{cls.post.pk}/comment': f'/posts/{cls.post.pk}/',
            f'/profile/{cls.not_author.username}/follow/':
            f'/profile/{cls.not_author.username}/',
            f'/profile/{cls.not_author.username}/unfollow/':
            f'/profile/{cls.not_author.username}/',
        }
        cls.open_url_names = [
            '/',
            '/group/test-slug/',
            f'/profile/{cls.user.username}/',
            f'/posts/{cls.post.pk}/',
        ]
        cls.guest_get_to_login = [
            '/create/',
            '/follow/',
            f'/posts/{cls.post.pk}/edit/',
            f'/posts/{cls.post.pk}/comment',
            f'/profile/{cls.user.username}/follow/',
            f'/profile/{cls.user.username}/unfollow/',
        ]
        cls.edit_post = f'/posts/{cls.post.pk}/edit/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.client_not_author = Client()
        self.authorized_client.force_login(self.user)
        self.client_not_author.force_login(self.not_author)

    def test_some_urls_redirect_guest_on_login(self):
        """
        Заданные в списке guest_get_to_login страницы
        перенаправят анонимного пользователя на страницу логина.
        """
        for address in self.guest_get_to_login:
            with self.subTest(address=address):
                cache.clear()
                response = self.guest_client.get(
                    address,
                    follow=True
                )
                self.assertRedirects(response, f'/auth/login/?next={address}')

    def test_post_edit_url_redirect_not_author_to_post_detail(self):
        """
        Страница /posts/post_id/edit/ перенаправит не автора поста
        на страницу просмотра поста.
        """
        response = self.client_not_author.get(
            self.edit_post,
            follow=True
        )
        self.assertRedirects(
            response, f'/posts/{self.post.pk}/'
        )

    def test_urls_uses_correct_template_and_open_pages(self):
        """
        Проверка, что URL-адрес использует соответствующий шаблон
        и все адреса доступны.
        """
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                cache.clear()
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_open_pages_for_guest(self):
        """
        Проверка, что общие адреса доступны
        не зарегистрированному пользователю.
        """
        for address in self.open_url_names:
            with self.subTest(address=address):
                cache.clear()
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_correct_status_for_users(self):
        """
        Проверка, что все адреса отвечают требуемыми кодами ответа
        зарегистрированному пользователю.
        """
        for address in self.authorized_url_status:
            with self.subTest(address=address):
                cache.clear()
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_correct_redirect_for_users(self):
        """
        Страницы /follow, /unfollow и /comment
        перенаправят зарегистрированного пользователя на правильную страницу.
        """
        for address, redirect in self.user_correct_community_redirect.items():
            with self.subTest(address=address):
                cache.clear()
                response = self.authorized_client.get(
                    address,
                    follow=True
                )
                self.assertRedirects(response, redirect)

    def test_connect_to_nonexistent_page(self):
        """
        Проверка, что URL-запрос к несуществующей странице
        вернёт ошибку 404.
        """
        response = self.guest_client.get('/nonexistent_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
