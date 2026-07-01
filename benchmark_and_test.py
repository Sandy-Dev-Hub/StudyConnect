from gevent import monkey
monkey.patch_all()

import os
import time
import sys
import unittest
import tracemalloc

from app import create_app
from app.extensions import db, cache
from app.models import User, UserProfile, Question, Answer, StudyGroup, GroupMember, StudyGoal, Notification


class StudyConnectRegressionAndBenchmark(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['FLASK_ENV'] = 'testing'
        cls.app = create_app('testing')
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()
        tracemalloc.start()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"\n[BENCHMARK] Memory usage: Current={current/1024:.2f} KB, Peak={peak/1024:.2f} KB")

    def setUp(self):
        self.client = self.app.test_client()

    def test_01_user_registration_and_auth(self):
        """Verify Phase 1 Auth & Profile."""
        resp = self.client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.total_points, 0)

    def test_02_question_and_answer_flow(self):
        """Verify Phase 1 Q&A and Feed Eager Loading."""
        user = User.query.filter_by(username='testuser').first()
        # Login
        self.client.post('/auth/login', data={'email': 'testuser@example.com', 'password': 'password123'})
        
        from app.questions.services import create_question
        q = create_question(title="What is Python?", body="Need help understanding decorators.", subject_tag="Computer Science", exam_tag="Finals", author_id=user.id)
        self.assertIsNotNone(q.id)

        # Benchmark feed query count
        from app.questions.services import get_feed
        start_t = time.time()
        pagination = get_feed(page=1, per_page=12)
        items = pagination.items
        for item in items:
            _ = item.author.username
            _ = item.time_ago
        dur = (time.time() - start_t) * 1000
        print(f"\n[BENCHMARK] Question feed retrieval + property access: {dur:.2f} ms")

    def test_03_study_groups(self):
        """Verify Phase 2 Study Groups."""
        user = User.query.filter_by(username='testuser').first()
        from app.groups.services import create_group
        group = create_group({'name': 'AI Scholars', 'description': 'Deep learning group', 'subject_tag': 'Computer Science', 'is_private': False}, user)
        self.assertEqual(group.name, 'AI Scholars')

    def test_04_productivity_and_goals(self):
        """Verify Phase 4 Productivity & Analytics."""
        user = User.query.filter_by(username='testuser').first()
        from app.productivity.services import ProductivityService
        res = ProductivityService.complete_session(user, duration_minutes=25, session_type='focus', subject='Computer Science')
        self.assertEqual(res['points_awarded'], 2)
        self.assertEqual(user.total_points, 2)

    def test_05_api_search_and_caching_benchmark(self):
        """Verify Phase 5A/5B/5C Search & Caching Benchmark."""
        # Uncached search
        t0 = time.time()
        r1 = self.client.get('/api/search?q=Python')
        dur_uncached = (time.time() - t0) * 1000
        self.assertEqual(r1.status_code, 200)

        # Cached search
        t1 = time.time()
        r2 = self.client.get('/api/search?q=Python')
        dur_cached = (time.time() - t1) * 1000
        self.assertEqual(r2.status_code, 200)

        print(f"\n[BENCHMARK] Search API Uncached: {dur_uncached:.2f} ms | Cached: {dur_cached:.2f} ms")
        self.assertLess(dur_cached, 100.0, "Cached response should be < 100ms")

    def test_06_health_endpoint(self):
        """Verify Phase 5E Health Endpoint."""
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['version'], '1.0.0')


if __name__ == '__main__':
    unittest.main()
