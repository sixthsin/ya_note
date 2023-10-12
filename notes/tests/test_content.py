from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

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

    def test_notes_for_different_users(self):
        """Тест проверки записей для разных пользователей."""
        note = (
            (self.author, True),
            (self.anybody, False),
        )
        url = reverse('notes:list')
        for user, dif_note in note:
            self.client.force_login(user)
            with self.subTest(user=user.username, note_in_list=dif_note):
                response = self.client.get(url)
                note_in_obj_list = self.note in response.context['object_list']
                self.assertIs(note_in_obj_list, dif_note)

    def test_form_in_page(self):
        """Тест что на страницу передается форма."""
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for page_name, args in urls:
            with self.subTest(page=page_name):
                url = reverse(page_name, args=args)
                self.client.force_login(self.author)
                response = self.client.get(url)
                self.assertIn('form', response.context)
