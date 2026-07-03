from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase

from apps.accounts.forms import SignupForm
from apps.accounts.models import User

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user_and_authenticate_by_email(self):
        """RF-02: login por e-mail + senha."""
        User.objects.create_user(email='tec@example.com', password='SenhaForte123', name='Tec')
        user = authenticate(username='tec@example.com', password='SenhaForte123')
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'tec@example.com')

    def test_email_unique(self):
        User.objects.create_user(email='tec@example.com', password='p', name='Tec')
        with self.assertRaises(Exception):
            User.objects.create_user(email='tec@example.com', password='p', name='Outro')

    def test_create_superuser(self):
        u = User.objects.create_superuser(email='admin@example.com', password='p', name='Admin')
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_superuser)


class SignupFormTest(TestCase):
    def test_valid_signup(self):
        form = SignupForm(data={
            'name': 'Novo', 'email': 'novo@example.com',
            'password1': 'SenhaForte123', 'password2': 'SenhaForte123',
        })
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        form = SignupForm(data={
            'name': 'Novo', 'email': 'novo@example.com',
            'password1': 'SenhaForte123', 'password2': 'diferente',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_duplicate_email(self):
        User.objects.create_user(email='dup@example.com', password='p', name='Dup')
        form = SignupForm(data={
            'name': 'Novo', 'email': 'dup@example.com',
            'password1': 'SenhaForte123', 'password2': 'SenhaForte123',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
