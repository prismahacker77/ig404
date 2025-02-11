import instaloader
import json
import os
import sys
import time
from datetime import datetime
from getpass import getpass
from instaloader.exceptions import TwoFactorAuthRequiredException, BadCredentialsException, LoginException

class IGUnfollowTracker:
    def __init__(self):
        """Initialize Instagram Unfollow Tracker"""
        self.username = os.getenv("INSTAGRAM_USER") or input("👤 Enter Instagram Username: ").strip()
        self.password = os.getenv("INSTAGRAM_PASS") or getpass("🔑 Enter Instagram Password: ")

        self.data_dir = "data"
        self.data_file = os.path.join(self.data_dir, "followers.json")
        self.session_file = os.path.join(self.data_dir, f"{self.username}_session")

        os.makedirs(self.data_dir, exist_ok=True)

        self.L = instaloader.Instaloader()
        self.L.context._session.headers.update({
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/537.36"
        })

        self._authenticate()

    def _authenticate(self):
        """Handles Instagram authentication with session management, 2FA, and backup codes"""
        if os.path.exists(self.session_file):
            try:
                self.L.load_session_from_file(self.username, self.session_file)
                print("✅ Session loaded successfully. Skipping login.")
                return
            except Exception as e:
                print(f"⚠️ Session error: {str(e)}. Removing session file.")
                os.remove(self.session_file)

        print("🔑 Attempting login...")

        try:
            self.L.login(self.username, self.password)
            self.L.save_session_to_file(self.session_file)
            print("✅ Login successful. Session saved.")
        except TwoFactorAuthRequiredException:
            self._handle_backup_code()
        except BadCredentialsException:
            print("❌ ERROR: Invalid credentials. Check your username and password.")
            sys.exit(1)
        except LoginException as e:
            print(f"❌ ERROR: Login failed: {str(e)}")
            sys.exit(1)
        except Exception as e:
            print(f"⚠️ Unexpected login error: {str(e)}")
            sys.exit(1)

    def _handle_backup_code(self):
        """Handles Instagram Backup Code Login"""
        print("\n🔒 2FA REQUIRED! Instagram is asking for an **8-digit backup code**.")
        print("📢 Go to Instagram App → Settings → Security → Two-Factor Authentication → Backup Codes")

        backup_code = input("🆘 Enter your **8-digit** backup code: ").strip()

        if len(backup_code) != 8 or not backup_code.isdigit():
            print("❌ ERROR: Invalid backup code format.")
            sys.exit(1)

        try:
            self.L.two_factor_login(backup_code)
            self.L.save_session_to_file(self.session_file)
            print("✅ Backup Code Accepted. Session saved.")
        except Exception as e:
            print(f"❌ ERROR: Backup Code failed: {e}")
            print("➡️ If login keeps failing, log in to Instagram manually and approve new login requests.")
            sys.exit(1)

    def get_followers(self):
        """Fetch current followers from Instagram"""
        try:
            profile = instaloader.Profile.from_username(self.L.context, self.username)
            return {follower.username for follower in profile.get_followers()}
        except Exception as e:
            print(f"⚠️ ERROR fetching followers: {str(e)}")
            return set()

    def load_previous_followers(self):
        """Load previous followers from file"""
        if not os.path.exists(self.data_file):
            return set()
        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)
                return set(data.get("followers", []))
        except json.JSONDecodeError:
            return set()

    def save_followers(self, followers):
        """Save current followers to file"""
        with open(self.data_file, "w") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "followers": list(followers)}, f, indent=2)

    def check_unfollowers(self):
        """Compare previous and current followers"""
        previous_followers = self.load_previous_followers()
        current_followers = self.get_followers()

        unfollowers = previous_followers - current_followers

        print("\n📊 Follower Analysis:")
        print(f"Current followers: {len(current_followers)}")
        print(f"Previous followers: {len(previous_followers)}")

        if unfollowers:
            print(f"\n🚨 {len(unfollowers)} users unfollowed you:")
            for username in unfollowers:
                print(f" • @{username}")
        else:
            print("\n✅ No unfollowers detected.")

        self.save_followers(current_followers)
        print(f"\n💾 Data saved to {self.data_file}")

if __name__ == "__main__":
    tracker = IGUnfollowTracker()

    # Ensure the session is open before running checks
    print("\n✅ Session is active. Checking for unfollowers...")
    while True:
        tracker.check_unfollowers()
        print("\n⏳ Waiting 5 minutes before next check...")
        time.sleep(300)  # Wait 5 minutes before running again