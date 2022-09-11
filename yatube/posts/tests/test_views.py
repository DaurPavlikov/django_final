import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='admin')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='img1.gif',
            content=image,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', args=('test-slug',)
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', args=(cls.user.username,)
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', args=(f'{cls.post.pk}',)
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', args=(f'{cls.post.pk}',)
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """Проверка, что URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_page_work_correct(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create',))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_page_work_correct(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=(self.post.pk,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('form', response.context)
        self.assertIn('post', response.context)
        self.assertIn('is_edit', response.context)
        form = response.context['form']
        is_edit = response.context['is_edit']
        post_object = response.context['post']
        post_text = post_object.text
        post_author = post_object.author
        post_group = post_object.group
        post_image = post_object.image
        group_title = post_group.title
        group_slug = post_group.slug
        group_description = post_group.description
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = form.fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_author, self.user)
        self.assertEqual(post_image, self.post.image)
        self.assertEqual(group_title, self.group.title)
        self.assertEqual(group_slug, self.group.slug)
        self.assertEqual(group_description, self.group.description)
        self.assertEqual(is_edit, True)

    def test_cache(self):
        """Проверяем, что страница кэшируется."""
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )
        response_first = self.client.get(reverse('posts:index'))
        post.delete()
        response_second = self.client.get(reverse('posts:index'))
        self.assertEqual(response_first.content, response_second.content)
        cache.clear()
        responce_third = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response_second.content, responce_third.content)


CNT_POSTS_FIRST_PAGE = 10
CNT_POSTS_SECOND_PAGE = 3
POST_ZERO = 0


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class DisplayingManyPostsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='admin')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='img1.gif',
            content=image,
            content_type='image/gif'
        )
        cls.bulk_posts = [
            Post(
                author=cls.user,
                text='Тестовый пост',
                group=cls.group,
                image=cls.uploaded
            ) for i in range(CNT_POSTS_FIRST_PAGE + CNT_POSTS_SECOND_PAGE)
        ]
        cls.posts = Post.objects.bulk_create(cls.bulk_posts)
        cls.testing_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', args=(cls.group.slug,)),
            reverse('posts:profile', args=(cls.user.username,))
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()

    def test_paginator_work(self):
        for reverse_name in self.testing_pages:
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertIn('page_obj', response.context)
                self.assertEqual(
                    len(response.context['page_obj']),
                    CNT_POSTS_FIRST_PAGE
                )
                response = self.client.get(reverse_name + '?page=2')
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertIn('page_obj', response.context)
                self.assertEqual(
                    len(response.context['page_obj']),
                    CNT_POSTS_SECOND_PAGE
                )

    def test_posts_pages_list(self):
        """
        На страницы index, group_list, profile
        передаётся ожидаемое количество объектов.
        """
        for reverse_name in self.testing_pages:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertIn('page_obj', response.context)
                self.assertEqual(
                    len(response.context['page_obj']),
                    CNT_POSTS_FIRST_PAGE
                )

    def page_obj_handler(self, response):
        self.assertIn('page_obj', response.context)
        post_object = response.context['page_obj'][POST_ZERO]
        post_text = post_object.text
        post_author = post_object.author
        post_group = post_object.group
        post_image = post_object.image
        group_title = post_group.title
        group_slug = post_group.slug
        group_description = post_group.description
        post_reference = self.posts[POST_ZERO]
        group_reference = self.posts[POST_ZERO].group
        self.assertEqual(post_text, post_reference.text)
        self.assertEqual(post_author.username, post_reference.author.username)
        self.assertEqual(post_image, f'{post_image.name}')
        self.assertEqual(group_title, group_reference.title)
        self.assertEqual(group_slug, group_reference.slug)
        self.assertEqual(group_description, group_reference.description)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.page_obj_handler(response)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('group', response.context)
        self.page_obj_handler(response)
        group_object = response.context['group']
        group_title = group_object.title
        group_slug = group_object.slug
        group_description = group_object.description
        group_reference = self.posts[POST_ZERO].group
        self.assertEqual(group_title, group_reference.title)
        self.assertEqual(group_slug, group_reference.slug)
        self.assertEqual(group_description, group_reference.description)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:profile', args=(self.user.username,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('following', response.context)
        self.assertIn('author', response.context)
        self.assertIn('count', response.context)
        self.page_obj_handler(response)
        following = response.context['following']
        username = response.context['author']
        count = response.context['count']
        post_reference = self.posts[POST_ZERO]
        self.assertEqual(username.username, post_reference.author.username)
        self.assertFalse(following)
        self.assertEqual(
            count,
            CNT_POSTS_FIRST_PAGE + CNT_POSTS_SECOND_PAGE
        )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        OFFSET = 1
        id_offset = POST_ZERO + OFFSET
        post = get_object_or_404(Post, pk=id_offset)
        response = self.client.get(
            reverse('posts:post_detail', args=(post.pk,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('post', response.context)
        self.assertIn('count', response.context)
        post = response.context['post']
        count = response.context['count']
        post_reference = self.posts[POST_ZERO]
        group_reference = self.posts[POST_ZERO].group
        self.assertEqual(post.text, post_reference.text)
        self.assertEqual(post.author.username, post_reference.author.username)
        self.assertEqual(post.image, f'{post_reference.image.name}')
        self.assertEqual(post.group.title, group_reference.title)
        self.assertEqual(post.group.slug, group_reference.slug)
        self.assertEqual(
            count,
            CNT_POSTS_FIRST_PAGE + CNT_POSTS_SECOND_PAGE,
        )


class PostsOfDifferentGroupsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='admin')
        cls.group_a = Group.objects.create(
            title='Тестовая группа A',
            slug='test-slug-a',
            description='Тестовое описание группы А',
        )
        cls.group_b = Group.objects.create(
            title='Тестовая группа B',
            slug='test-slug-b',
            description='Тестовое описание группы В',
        )
        cls.post_a = Post.objects.create(
            author=cls.user,
            text='Тестовый пост группы А',
            group=cls.group_a,
        )
        cls.post_b = Post.objects.create(
            author=cls.user,
            text='Тестовый пост группы B',
            group=cls.group_b,
        )
        cls.testing_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', args=(cls.group_a.slug,)),
            reverse('posts:group_list', args=(cls.group_b.slug,)),
            reverse('posts:profile', args=(cls.user.username,)),
        ]

    def setUp(self):
        self.client = Client()

    def test_verification_creating_post(self):
        """
        Проверяем, что если при создании поста указать группу,
        то этот пост появляется на:
            главной странице сайта,
            на странице выбранной группы,
            в профайле пользователя.
        Проверяем, что пост не попал в группу, для которой не был предназначен.
        """
        for reverse_name in self.testing_pages:
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertIn('page_obj', response.context)
                for post in response.context['page_obj']:
                    if post != self.post_b:
                        self.assertEqual(post, self.post_a)
                    else:
                        self.assertEqual(post, self.post_b)


class FollowsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='author')
        cls.user_follower = User.objects.create_user(username='follower')
        cls.user_notfollower = User.objects.create_user(username='notfollower')
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_user_author = Client()
        self.authorized_user_follower = Client()
        self.authorized_user_notfollower = Client()
        self.authorized_user_author.force_login(self.user_author)
        self.authorized_user_follower.force_login(self.user_follower)
        self.authorized_user_notfollower.force_login(self.user_notfollower)

    def test_following(self):
        """
        Проверяем, что авторизованный пользователь
        может подписываться на других пользователей.
        """
        response = self.authorized_user_follower.get(
            reverse('posts:profile_follow', args=(self.user_author,))
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        follow = Follow.objects.first()
        self.assertTrue(follow)
        self.assertEqual(follow.user, self.user_follower)
        self.assertEqual(follow.author, self.user_author)

    def test_unfollowing(self):
        """
        Проверяем, что авторизованный пользователь может отписаться
        от других пользователей.
        """
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_author,
        )
        response = self.authorized_user_follower.get(
            reverse('posts:profile_unfollow', args=(self.user_author,))
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        follow = Follow.objects.first()
        self.assertFalse(follow)

    def test_new_post_appear_for_followers(self):
        """
        Проверяем, что новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан.
        """
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_author,
        )
        count_author_posts = Post.objects.count()
        follower_response = self.authorized_user_follower.get(
            reverse('posts:follow_index')
        )
        notfollower_response = self.authorized_user_notfollower.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(follower_response.status_code, HTTPStatus.OK)
        self.assertEqual(notfollower_response.status_code, HTTPStatus.OK)
        self.assertEqual(
            len(follower_response.context['page_obj']),
            count_author_posts,
        )
        self.assertNotEqual(
            len(notfollower_response.context['page_obj']),
            count_author_posts,
        )
