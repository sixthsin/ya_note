from http import HTTPStatus

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class Testroutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Имя Фамилия')
        cls.anybody = User.objects.create(username='Кто То')
        cls.note = Note.objects.create(
            title='Название',
            text='Текст',
            slug='slug',
            author=cls.author,
        )

    def test_anonymous_user_page_availability(self):
        """Доступность главной страницы, страницы логина, выхода и
        входа для анонимного пользователя."""
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )
        for page_name in urls:
            with self.subTest(page=page_name):
                url = reverse(page_name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_user_pages_availability(self):
        """Доступность страниц списка записей, успешного выполнения,
        добавления записи для авторизированного пользователя."""
        urls = (
            'notes:list',
            'notes:success',
            'notes:add',
        )
        self.client.force_login(self.author)
        for page_name in urls:
            with self.subTest(page=page_name):
                url = reverse(page_name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_delete_note_only_for_author(self):
        """Страницы подробности записей, удаления и изменения достпно
        только автору записи."""
        users_status = (
            (self.author, HTTPStatus.OK),
            (self.anybody, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_status:
            self.client.force_login(user)
            for page in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(user=user.username, page=page):
                    url = reverse(page, args=[self.note.slug])
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Доступность перенаправлений для анонимного пользователя."""
        login_url = reverse('users:login')
        urls = (
            ('notes:list', None),
            ('notes:success', None),
            ('notes:add', None),
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        for page_name, args in urls:
            with self.subTest(page=page_name):
                url = reverse(page_name, args=args)
                response = self.client.get(url)
                self.assertRedirects(response, f'{login_url}?next={url}')
