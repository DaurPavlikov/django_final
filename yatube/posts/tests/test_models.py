from django.test import TestCase

from ..models import Group, Post, User


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
            text='Тестовый пост',
        )

    def test_post_model_have_correct_object_name(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        CROPPING_LIMIT = 15
        self.assertEqual(
            str(PostModelTest.post),
            PostModelTest.post.text[:CROPPING_LIMIT],
            'Вывод __str__ модели Post не соответствует обрезанному полю text.'
        )

    def test_group_model_have_correct_object_name(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        self.assertEqual(
            str(PostModelTest.group),
            PostModelTest.group.title,
            'Вывод __str__ модели Group не соответствует полю title.'
        )
