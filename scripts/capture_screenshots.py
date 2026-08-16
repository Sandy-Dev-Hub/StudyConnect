"""
capture_screenshots.py
======================
Automated desktop and mobile screenshot capture for the StudyConnect app.

Usage:
    python scripts/capture_screenshots.py [BASE_URL]

    BASE_URL defaults to http://localhost:5000 if not supplied.
"""

import sys
import os
import pathlib
import base64

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:5000"
SCREENSHOTS_DIR = pathlib.Path(__file__).parent.parent / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

MOCK_LAT = 13.0827
MOCK_LNG = 80.2707
MOCK_ACCURACY = 20

USER1_USERNAME = "nearby_user_1"
USER1_EMAIL = "nearby1@test.com"
USER1_PASSWORD = "pass123"

USER2_USERNAME = "nearby_user_2"
USER2_EMAIL = "nearby2@test.com"
USER2_PASSWORD = "pass123"

def seed_data():
    print("[seed] Setting up test users and peer location...")
    project_root = pathlib.Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    from app import create_app
    from app.extensions import db
    from app.models import User
    from app.nearby.services import LocationService

    app = create_app()
    
    routes_to_capture = []
    for rule in app.url_map.iter_rules():
        rule_str = str(rule)
        if 'GET' in rule.methods and not rule.arguments:
            if not rule_str.startswith('/api/') and '/api/' not in rule_str and not rule_str.startswith('/static') and not rule_str.startswith('/admin'):
                routes_to_capture.append(rule_str)
                
    with app.app_context():
        u1 = User.query.filter_by(username=USER1_USERNAME).first()
        if not u1:
            u1 = User(username=USER1_USERNAME, email=USER1_EMAIL)
            u1.set_password(USER1_PASSWORD)
            db.session.add(u1)
            print(f"[seed] Created {USER1_USERNAME}")
        else:
            u1.set_password(USER1_PASSWORD)

        u2 = User.query.filter_by(username=USER2_USERNAME).first()
        if not u2:
            u2 = User(username=USER2_USERNAME, email=USER2_EMAIL)
            u2.set_password(USER2_PASSWORD)
            db.session.add(u2)
            print(f"[seed] Created {USER2_USERNAME}")

        db.session.commit()

        nearby_lat = MOCK_LAT + 0.004
        nearby_lng = MOCK_LNG + 0.003
        try:
            LocationService.share_location(
                user_id=u2.id, lat=nearby_lat, lng=nearby_lng,
                subject_tag="Physics", exam_tag="JEE", accuracy=MOCK_ACCURACY,
            )
            print(f"[seed] Seeded {USER2_USERNAME} location at ({nearby_lat:.4f}, {nearby_lng:.4f})")
        except Exception as exc:
            print(f"[seed] Location seed skipped ({exc})")

    return list(set(routes_to_capture))

def capture_via_cdp(target_page, name, clip=None):
    try:
        cdp = target_page.context.new_cdp_session(target_page)
        if clip:
            clip_dict = {"x": clip["x"], "y": clip["y"], "width": clip["width"], "height": clip["height"], "scale": 1}
            res = cdp.send("Page.captureScreenshot", {"clip": clip_dict})
        else:
            res = cdp.send("Page.captureScreenshot")
            
        with open(SCREENSHOTS_DIR / name, "wb") as f:
            f.write(base64.b64decode(res["data"]))
        cdp.detach()
    except Exception as e:
        print(f"[screenshot] CDP capture error for {name}: {e}")

def slugify_route(route: str) -> str:
    if route == "/": return "landing"
    clean = route.strip("/")
    if not clean: return "landing"
    return clean.replace("/", "-")

    filename = f"{prefix}-{name}.png"
    print(f"[screenshot] Capturing {filename} ...")
    try:
        page.goto(url, wait_until="networkidle")
        page.add_style_tag(content="#onboardingModal, .modal-backdrop { display: none !important; opacity: 0 !important; visibility: hidden !important; }")
        page.wait_for_timeout(2000)
        capture_via_cdp(page, filename)
    except Exception as e:
        print(f"[error] Failed to capture {filename}: {e}")

def capture(base_url: str, routes: list):
    from playwright.sync_api import sync_playwright, expect

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        
        desktop_ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            geolocation={"latitude": MOCK_LAT, "longitude": MOCK_LNG, "accuracy": MOCK_ACCURACY},
            permissions=["geolocation"],
        )
        iphone = pw.devices['iPhone 13']
        mobile_ctx = browser.new_context(
            **iphone,
            geolocation={"latitude": MOCK_LAT, "longitude": MOCK_LNG, "accuracy": MOCK_ACCURACY},
            permissions=["geolocation"],
        )
        
        desktop_page = desktop_ctx.new_page()
        mobile_page = mobile_ctx.new_page()

        # Capture only the 5 essential routes requested by the user
        routes_to_capture = [
            "/",
            "/questions",
            "/nearby",
            "/groups",
            "/productivity"
        ]
        
        # Unauthenticated captures
        capture_page(desktop_page, f"{base_url}/", "landing", is_mobile=False)
        capture_page(mobile_page, f"{base_url}/", "landing", is_mobile=True)

        print(f"[browser] Logging in as {USER1_USERNAME} on desktop ...")
        desktop_page.goto(f"{base_url}/auth/login", wait_until="networkidle")
        email_input = desktop_page.locator("input[name='email']")
        if email_input.count() > 0:
            email_input.fill(USER1_EMAIL)
        else:
            desktop_page.locator("input[name='username']").fill(USER1_USERNAME)
        desktop_page.locator("input[name='password']").fill(USER1_PASSWORD)
        desktop_page.locator("button[type='submit']").click()
        desktop_page.wait_for_url(f"{base_url}/**", wait_until="networkidle")
        
        print(f"[browser] Logging in as {USER1_USERNAME} on mobile ...")
        mobile_page.goto(f"{base_url}/auth/login", wait_until="networkidle")
        email_input = mobile_page.locator("input[name='email']")
        if email_input.count() > 0:
            email_input.fill(USER1_EMAIL)
        else:
            mobile_page.locator("input[name='username']").fill(USER1_USERNAME)
        mobile_page.locator("input[name='password']").fill(USER1_PASSWORD)
        mobile_page.locator("button[type='submit']").click()
        mobile_page.wait_for_url(f"{base_url}/**", wait_until="networkidle")

        # Capture authenticated routes
        auth_routes_to_capture = [r for r in routes_to_capture if r != "/"]
        for r in auth_routes_to_capture:
            name = slugify_route(r)
            capture_page(desktop_page, f"{base_url}{r}", name, is_mobile=False)
            capture_page(mobile_page, f"{base_url}{r}", name, is_mobile=True)
            
        print("[browser] Running Nearby custom capture...")
        
        def capture_locator(page, loc, name, fallback_clip=None):
            try:
                box = loc.evaluate("el => { const rect = el.getBoundingClientRect(); return {x: rect.x, y: rect.y, width: rect.width, height: rect.height}; }", timeout=2000)
                if box and box.get("width", 0) > 0:
                    capture_via_cdp(page, name, box)
                else:
                    if fallback_clip:
                        capture_via_cdp(page, name, fallback_clip)
                    else:
                        capture_via_cdp(page, name)
            except Exception as e:
                print(f"[screenshot] Error capturing {name}: {e}")

        try:
            csrf_token = desktop_page.evaluate("document.querySelector('meta[name=\"csrf-token\"]')?.getAttribute('content') || ''")
            desktop_page.evaluate(f"""async () => {{
                await fetch('/nearby/api/share', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json', 'X-CSRFToken': '{csrf_token}'}},
                    body: JSON.stringify({{lat: {MOCK_LAT}, lng: {MOCK_LNG}, accuracy: {MOCK_ACCURACY}, subject: 'Physics', exam: 'JEE'}})
                }});
            }}""")
            
            active_page = desktop_ctx.new_page()
            active_page.goto(f"{base_url}/nearby/", wait_until="networkidle")
            active_page.add_style_tag(content="* { animation: none !important; transition: none !important; }")
            expect(active_page.locator("#statusTitle")).to_have_text("Location Sharing Active", timeout=15_000)
            
            print("[screenshot] laptop-hero.png ...")
            capture_locator(active_page, active_page.locator(".container.py-4 > div:first-child"), "laptop-hero.png", {"x": 0, "y": 0, "width": 1440, "height": 250})
            
            print("[screenshot] laptop-share-panel.png ...")
            capture_locator(active_page, active_page.locator(".nearby-control-bar"), "laptop-share-panel.png")
            
            print("[screenshot] laptop-filters.png ...")
            filter_bar_active = active_page.locator("#filterRadius").locator("..")
            if filter_bar_active.count() > 0:
                capture_locator(active_page, active_page.locator("#filterRadius").locator("..").locator(".."), "laptop-filters.png")
                
            print("[screenshot] laptop-nearby-list.png ...")
            students_sidebar = active_page.locator(".students-sidebar")
            expect(students_sidebar).to_be_visible(timeout=10_000)
            active_page.wait_for_timeout(2500)
            capture_locator(active_page, students_sidebar, "laptop-nearby-list.png")
            
            print("[screenshot] laptop-full-page.png ...")
            capture_via_cdp(active_page, "laptop-full-page.png")
            active_page.close()
        except Exception as e:
            print(f"[error] Nearby custom capture failed: {e}")

        desktop_ctx.close()
        mobile_ctx.close()
        browser.close()

if __name__ == "__main__":
    routes = seed_data()
    capture(BASE_URL, routes)
