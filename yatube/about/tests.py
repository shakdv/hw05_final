from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticURLTests(TestCase):
    def setUp(self):
        self.user_guest = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности любому пользователю адресов about/*."""
        url_status_code = {
            reverse('about:author'): HTTPStatus.OK,
            reverse('about:tech'): HTTPStatus.OK,
        }
        for address, code in url_status_code.items():
            with self.subTest(address=address):
                response = self.user_guest.get(address).status_code
                self.assertEqual(response, code)

    def test_about_url_uses_correct_template(self):
        """URL-адрес использует соответствующие шаблоны about/*."""
        templates_url_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.user_guest.get(address)
                self.assertTemplateUsed(response, template)
