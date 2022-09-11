from django.contrib.auth import get_user_model
from django.test import Client, TestCase


User = get_user_model()


class CustomErrorPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='admin')

    def setUp(self):
        self.client = Client()

    def test_custom_404_page_use_correct_template(self):
        """
        Страница /nonexistent/ перенаправит анонимного пользователя
        на кастомную страницу 404.
        """
        response = self.client.get('/nonexistent/', follow=True)
        self.assertTemplateUsed(response, 'core/404.html')
