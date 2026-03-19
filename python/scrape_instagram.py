"""
Instagram scraper — fetches post count & follower count for given profile URLs
and stores results in Supabase.

First run:
  1. Copy .env.example → .env and fill in your Supabase credentials.
  2. pip install -r requirements.txt
  3. python scrape_instagram.py
     The browser will open. Log in to Instagram manually, then press ENTER here.

Subsequent runs:
  The saved Chrome profile reuses your session automatically (no login needed).
"""


import re
import time
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from supabase import create_client, Client


# ── Supabase ────────────────────────────────────────────────────────────────
SUPABASE_URL="https://umftzelcpclkbmewoehr.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVtZnR6ZWxjcGNsa2JtZXdvZWhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM2NjI2NDksImV4cCI6MjA4OTIzODY0OX0.JF6X-u3XEvorLTlgCtGIJxwbJGvb8YBbfrH-DI6ppHk"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("Set SUPABASE_URL and SUPABASE_KEY in your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Profile URLs to scrape ───────────────────────────────────────────────────
# Add or remove Instagram profile URLs here.
PROFILE_URLS = [
    "https://www.instagram.com/magalirmandram2.0/",
    "https://www.instagram.com/ambedkarapproved/",
    # "https://www.instagram.com/your_account/",
]

# ── Chrome profile dir (persists login session) ──────────────────────────────
CHROME_PROFILE_DIR = Path(__file__).parent / "chrome_profile"


def parse_count(text: str) -> int | None:
    """Convert strings like '1,234', '12.5K', '3.1M' to an integer."""
    text = text.strip().replace(",", "")
    m = re.match(r"([\d.]+)\s*([KkMmBb]?)", text)
    if not m:
        return None
    num = float(m.group(1))
    suffix = m.group(2).upper()
    multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(suffix, 1)
    return int(num * multiplier)


def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


def ensure_logged_in(driver: webdriver.Chrome):
    """Open Instagram home. If not logged in, wait for the user to log in manually."""
    driver.get("https://www.instagram.com/")
    time.sleep(3)

    # Check whether we're already logged in
    if "login" in driver.current_url or driver.find_elements(By.NAME, "username"):
        print("\n[ACTION REQUIRED] Log in to Instagram in the browser window.")
        input("Press ENTER here once you are logged in… ")
        time.sleep(2)
    else:
        print("[INFO] Already logged in via saved session.")


def _exact_count_from_li(li) -> int | None:
    """
    Extract the exact number from a stat <li> element.
    Instagram sets a `title` attribute on the number <span> with the full
    unabbreviated value, e.g. title="1,234,567". We prefer that over the
    visible abbreviated text (e.g. "1.2M").
    """
    # Prefer span with title attribute (exact number)
    for span in li.find_elements(By.CSS_SELECTOR, "span[title]"):
        title = span.get_attribute("title")
        if title and re.search(r"\d", title):
            return parse_count(title)
    # Fallback: first span whose text is numeric
    for span in li.find_elements(By.TAG_NAME, "span"):
        text = span.text.strip()
        if re.search(r"\d", text):
            return parse_count(text)
    return None


def scrape_profile(driver: webdriver.Chrome, url: str) -> dict | None:
    driver.get(url)
    time.sleep(4)  # give JS time to fully render

    username = url.rstrip("/").split("/")[-1]

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "header section ul"))
        )
    except Exception:
        print(f"[WARN] Timed out waiting for stats on {url}")
        return None

    posts = None
    followers = None

    # ── Method 1: find each <li> by its label text ───────────────────────────
    # This is the most accurate method — we locate "posts" and "followers"
    # labels explicitly instead of relying on positional index.
    try:
        lis = driver.find_elements(By.CSS_SELECTOR, "header section ul li")
        for li in lis:
            label = li.text.lower()
            if "post" in label:
                posts = _exact_count_from_li(li)
            elif "follower" in label:
                followers = _exact_count_from_li(li)
    except Exception as e:
        print(f"[WARN] Method 1 (label-based) failed: {e}")

    # ── Method 2: parse embedded JSON in <script> tags ───────────────────────
    # Instagram bakes profile data as JSON inside the page.
    if posts is None or followers is None:
        try:
            raw = driver.execute_script("""
                for (const s of document.querySelectorAll('script[type="application/json"]')) {
                    const t = s.textContent;
                    if (t.includes('edge_followed_by') || t.includes('follower_count'))
                        return t;
                }
                return null;
            """)
            if raw:
                def find_values(obj, keys):
                    """Recursively walk JSON for the first matching keys."""
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if k in keys and isinstance(v, (int, float)):
                                yield k, int(v)
                            yield from find_values(v, keys)
                    elif isinstance(obj, list):
                        for item in obj:
                            yield from find_values(item, keys)

                data = json.loads(raw)
                found = dict(find_values(data, {
                    "edge_followed_by", "follower_count",
                    "edge_owner_to_timeline_media", "media_count",
                }))
                if followers is None:
                    followers = (
                        found.get("edge_followed_by")
                        or found.get("follower_count")
                    )
                if posts is None:
                    posts = (
                        found.get("edge_owner_to_timeline_media")
                        or found.get("media_count")
                    )
        except Exception as e:
            print(f"[WARN] Method 2 (JSON) failed: {e}")

    # ── Method 3: meta description (last resort, may be abbreviated) ─────────
    if posts is None or followers is None:
        try:
            meta = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
            content = meta.get_attribute("content")
            posts_match = re.search(r"([\d,.]+[KkMmBb]?)\s+Posts?", content, re.I)
            followers_match = re.search(r"([\d,.]+[KkMmBb]?)\s+Followers?", content, re.I)
            if posts is None and posts_match:
                posts = parse_count(posts_match.group(1))
            if followers is None and followers_match:
                followers = parse_count(followers_match.group(1))
        except Exception as e:
            print(f"[WARN] Method 3 (meta) failed: {e}")

    if posts is None and followers is None:
        print(f"[ERROR] Could not extract stats for {url}")
        return None

    return {"username": username, "profile_url": url, "posts": posts, "followers": followers}


def save_to_supabase(record: dict):
    response = supabase.table("instagram_stats").insert(record).execute()
    print(f"  [DB] Saved — {record['username']}: {record['followers']:,} followers, {record['posts']:,} posts")


def main():
    driver = build_driver()
    try:
        ensure_logged_in(driver)

        for url in PROFILE_URLS:
            print(f"\nScraping: {url}")
            data = scrape_profile(driver, url)
            if data:
                print(f"  followers={data['followers']}, posts={data['posts']}")
                save_to_supabase(data)
            else:
                print(f"  Skipped (no data).")
            time.sleep(2)  # polite delay between requests

    finally:
        driver.quit()

    print("\nDone.")


if __name__ == "__main__":
    main()
