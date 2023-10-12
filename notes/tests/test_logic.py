from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING

User = get_user_model()

NOTE_TITLE = 'Заголовок'
NEW_NOTE_TITLE = 'Новый заголовок'
NOTE_TEXT = 'Текст'
NEW_NOTE_TEXT = 'Новый текст'
FORM_SLUG = 'form-slug'
NOTE_SLUG = 'note-slug'
NEW_NOTE_SLUG = 'new-note-slug'


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Имя Фамилия')
        cls.url = reverse('notes:add')
        cls.client = Client()
        cls.client.force_login(cls.user)
        cls.form_data = {
            'title': NOTE_TITLE,
            'text': NOTE_TEXT,
            'slug': FORM_SLUG,
        }

    def test_user_can_create_note(self):
        """Тест для проверки создания записи."""
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)

        new_note = Note.objects.filter(slug=self.form_data['slug']).first()
        self.assertEqual(new_note.author, self.user)
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])

    def test_anonymous_user_cant_create_note(self):
        """Тест что анонимный пользователь не сможет создать запись."""
        response = self.client.post(self.url, data=self.form_data)
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={self.url}')
        self.assertEqual(Note.objects.count(), 0)

    def test_slug_is_unique(self):
        """Проверка уникальности слага."""
        self.client.force_login(self.user)
        self.client.post(self.url, data=self.form_data)
        response = self.client.post(self.url, data=self.form_data)
        warning = self.form_data['slug'] + WARNING
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=warning
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """Проверка работы с пустым слагом."""
        del self.form_data['slug']
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)

        expected_slug = slugify(self.form_data['title'])
        new_note = Note.objects.filter(slug=expected_slug).first()
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditAndDelete(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Имя Фамилия')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.anybody = User.objects.create(username='Кто То')
        cls.anybody_client = Client()
        cls.anybody_client.force_login(cls.anybody)
        cls.note = Note.objects.create(
            title=NOTE_TITLE,
            text=NOTE_TEXT,
            slug=NOTE_SLUG,
            author=cls.author,
        )
        cls.edit_note_url = reverse('notes:edit', args=[cls.note.slug])
        cls.delete_note_url = reverse('notes:delete', args=[cls.note.slug])
        cls.form_data = {
            'title': NEW_NOTE_TITLE,
            'text': NEW_NOTE_TEXT,
            'slug': NEW_NOTE_SLUG,
        }

    def test_author_can_edit_note(self):
        """Автор может изменить запись."""
        self.author_client.post(self.edit_note_url, self.form_data)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, NEW_NOTE_TITLE)
        self.assertEqual(self.note.text, NEW_NOTE_TEXT)
        self.assertEqual(self.note.slug, NEW_NOTE_SLUG)

    def test_author_can_delete_note(self):
        """Автор может удалить запись."""
        response = self.author_client.post(self.delete_note_url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_edit_note(self):
        """Случайный пользователь не может изменить чужую запись."""
        response = self.anybody_client.post(self.edit_note_url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.note.refresh_from_db()
        self.assertEqual(self.note.title, NOTE_TITLE)
        self.assertEqual(self.note.text, NOTE_TEXT)
        self.assertEqual(self.note.slug, NOTE_SLUG)

    def test_other_user_cant_delete_note(self):
        """Случайный пользователь не может удалить чужую запись."""
        response = self.anybody_client.post(self.delete_note_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
