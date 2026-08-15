"""
Regression test: Verify that the IP geolocation fallback has been fully removed
from the Nearby Students feature.

Acceptance criteria verified here:
  1. GET /nearby/api/ip-location returns 404 (endpoint deleted).
  2. LocationService no longer has a resolve_ip_location attribute.
  3. No reference to ipapi.co exists anywhere under app/nearby/.
"""

import os
import sys
import unittest

# ── path setup ──────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from app import create_app


class NearbyIPRemovedTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'LOGIN_DISABLED': False,
        })
        cls.client = cls.app.test_client()

    # ── 1. HTTP endpoint must not exist ──────────────────────────────────────
    def test_ip_location_endpoint_returns_404(self):
        """GET /nearby/api/ip-location must no longer be registered."""
        resp = self.client.get('/nearby/api/ip-location')
        self.assertEqual(
            resp.status_code, 404,
            msg=(
                f"Expected 404 (endpoint deleted), got {resp.status_code}. "
                "The /nearby/api/ip-location route was not removed from routes.py."
            )
        )
        print("[PASS] GET /nearby/api/ip-location -> 404")

    # ── 2. Service method must not exist ─────────────────────────────────────
    def test_resolve_ip_location_method_absent(self):
        """LocationService must no longer expose resolve_ip_location."""
        from app.nearby.services import LocationService
        self.assertFalse(
            hasattr(LocationService, 'resolve_ip_location'),
            msg=(
                "LocationService.resolve_ip_location still exists. "
                "Remove the method from app/nearby/services.py."
            )
        )
        print("[PASS] LocationService.resolve_ip_location is absent")

    # ── 3. No ipapi.co reference in app/nearby/ ───────────────────────────────
    def test_no_ipapi_reference_in_nearby_package(self):
        """No file under app/nearby/ should reference ipapi.co."""
        nearby_dir = os.path.join(ROOT, 'app', 'nearby')
        offending = []
        for fname in os.listdir(nearby_dir):
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(nearby_dir, fname)
            with open(fpath, encoding='utf-8') as f:
                content = f.read()
            if 'ipapi.co' in content or 'ip-api.com' in content:
                offending.append(fname)
        self.assertEqual(
            offending, [],
            msg=(
                f"Found ipapi.co / ip-api.com references in: {offending}. "
                "Remove all IP-geolocation references."
            )
        )
        print("[PASS] No ipapi.co / ip-api.com references in app/nearby/")

    # ── 4. No resolve_ip_location reference in any .py under app/ ────────────
    def test_no_resolve_ip_location_calls_in_app(self):
        """No Python file under app/ should call or import resolve_ip_location."""
        app_dir = os.path.join(ROOT, 'app')
        offending = []
        for dirpath, _, filenames in os.walk(app_dir):
            for fname in filenames:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(dirpath, fname)
                with open(fpath, encoding='utf-8') as f:
                    content = f.read()
                if 'resolve_ip_location' in content:
                    offending.append(os.path.relpath(fpath, ROOT))
        self.assertEqual(
            offending, [],
            msg=(
                f"Found resolve_ip_location references in: {offending}. "
                "Remove all calls to this deleted method."
            )
        )
        print("[PASS] No resolve_ip_location references found anywhere in app/")


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(NearbyIPRemovedTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
