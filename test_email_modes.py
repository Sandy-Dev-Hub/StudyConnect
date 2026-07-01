from gevent import monkey
monkey.patch_all()

import unittest
from unittest.mock import patch
from app import create_app
from app.extensions import db, mail
from app.models import User
import io
import sys


class TestEmailModes(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['AUTO_VERIFY_USERS'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_mail_suppress_send_true(self):
        """Verify behavior when MAIL_SUPPRESS_SEND is True (Development Mode behavior)."""
        self.app.config['MAIL_SUPPRESS_SEND'] = True
        self.app.config['DEBUG'] = True
        client = self.app.test_client()

        with patch.object(mail, 'send') as mock_send:
            # 1. Registration
            captured_stdout = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured_stdout
            try:
                resp = client.post('/auth/register', data={
                    'username': 'user_suppress',
                    'email': 'suppress@example.com',
                    'password': 'password123',
                    'confirm_password': 'password123'
                }, follow_redirects=True)
            finally:
                sys.stdout = old_stdout

            output = captured_stdout.getvalue()
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Check the console for the verification link.', resp.data)
            mock_send.assert_not_called()
            self.assertIn('EMAIL VERIFICATION', output)
            self.assertIn('suppress@example.com', output)

            # 2. Unverified login attempt
            resp = client.post('/auth/login', data={
                'email': 'suppress@example.com',
                'password': 'password123'
            }, follow_redirects=True)
            self.assertIn(b'Check the console for the verification link.', resp.data)

            # 3. Forgot Password
            captured_stdout = io.StringIO()
            sys.stdout = captured_stdout
            try:
                resp = client.post('/auth/forgot-password', data={
                    'email': 'suppress@example.com'
                }, follow_redirects=True)
            finally:
                sys.stdout = old_stdout

            self.assertIn(b'check the console for the reset link.', resp.data)
            mock_send.assert_not_called()
            self.assertIn('PASSWORD RESET', captured_stdout.getvalue())

            # 4. Resend verification
            user = User.query.filter_by(email='suppress@example.com').first()
            user.is_verified = True
            db.session.commit()
            client.post('/auth/login', data={'email': 'suppress@example.com', 'password': 'password123'}, follow_redirects=True)
            user.is_verified = False
            db.session.commit()

            captured_stdout = io.StringIO()
            sys.stdout = captured_stdout
            try:
                resp = client.get('/auth/resend-verification', follow_redirects=True)
            finally:
                sys.stdout = old_stdout

            self.assertIn(b'Check the console for the verification link.', resp.data)

    def test_mail_suppress_send_false(self):
        """Verify behavior when MAIL_SUPPRESS_SEND is False (Production Mode behavior even if DEBUG=True)."""
        self.app.config['MAIL_SUPPRESS_SEND'] = False
        self.app.config['BREVO_API_KEY'] = 'test_brevo_key'
        self.app.config['DEBUG'] = True
        client = self.app.test_client()

        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"messageId": "123"}'

        with patch('app.auth.services.requests.post', return_value=mock_response) as mock_post:
            # 1. Registration
            captured_stdout = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured_stdout
            try:
                resp = client.post('/auth/register', data={
                    'username': 'user_real',
                    'email': 'real@example.com',
                    'password': 'password123',
                    'confirm_password': 'password123'
                }, follow_redirects=True)
            finally:
                sys.stdout = old_stdout

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Please check your email for the verification link.', resp.data)
            self.assertEqual(mock_post.call_count, 1)
            payload = mock_post.call_args[1]['json']
            self.assertEqual(payload['to'][0]['email'], 'real@example.com')
            self.assertIn('Verify Your Email', payload['subject'])

            output = captured_stdout.getvalue()
            self.assertNotIn('EMAIL VERIFICATION', output)

            # 2. Unverified login attempt
            resp = client.post('/auth/login', data={
                'email': 'real@example.com',
                'password': 'password123'
            }, follow_redirects=True)
            self.assertIn(b'Please check your email for the verification link.', resp.data)

            # 3. Forgot Password
            mock_post.reset_mock()
            captured_stdout = io.StringIO()
            sys.stdout = captured_stdout
            try:
                resp = client.post('/auth/forgot-password', data={
                    'email': 'real@example.com'
                }, follow_redirects=True)
            finally:
                sys.stdout = old_stdout

            self.assertIn(b'please check your email for the reset link.', resp.data)
            self.assertEqual(mock_post.call_count, 1)
            payload = mock_post.call_args[1]['json']
            self.assertEqual(payload['to'][0]['email'], 'real@example.com')
            self.assertIn('Reset Your Password', payload['subject'])
            self.assertNotIn('PASSWORD RESET', captured_stdout.getvalue())

            # 4. Resend verification
            mock_post.reset_mock()
            user = User.query.filter_by(email='real@example.com').first()
            user.is_verified = True
            db.session.commit()
            client.post('/auth/login', data={'email': 'real@example.com', 'password': 'password123'}, follow_redirects=True)
            user.is_verified = False
            db.session.commit()

            captured_stdout = io.StringIO()
            sys.stdout = captured_stdout
            try:
                resp = client.get('/auth/resend-verification', follow_redirects=True)
            finally:
                sys.stdout = old_stdout

            self.assertIn(b'Please check your email for the verification link.', resp.data)
            self.assertEqual(mock_post.call_count, 1)


if __name__ == '__main__':
    unittest.main()
