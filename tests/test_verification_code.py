import os
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault(
    "DATABASE_PATH",
    os.path.join(tempfile.mkdtemp(prefix="outlookemail-tests-"), "test.db"),
)

import web_outlook_app as app_module


ACTIVE_ACCOUNT = {
    "id": 1,
    "email": "user@outlook.com",
    "status": "active",
    "account_type": "outlook",
    "provider": "outlook",
    "imap_host": "outlook.live.com",
    "imap_password": "not-used-by-graph",
}

IMAP_ACCOUNT = {
    "id": 3,
    "email": "imap-user@example.com",
    "status": "active",
    "account_type": "imap",
    "provider": "custom",
    "imap_host": "imap.example.com",
    "imap_password": "imap-secret",
    "imap_port": 993,
}

OAUTH_IMAP_ACCOUNT = {
    "id": 4,
    "email": "oauth-imap-user@outlook.com",
    "status": "active",
    "account_type": "imap",
    "provider": "outlook",
    "client_id": "oauth-client-id",
    "refresh_token": "oauth-refresh-token",
    "imap_host": "outlook.live.com",
    "imap_password": "unused-in-oauth-imap",
    "imap_port": 993,
}

GROUP_RECORD = {
    "id": 2,
    "name": "注册组",
    "description": "用于注册流程",
    "color": "#123456",
    "is_system": 0,
    "proxy_url": "",
}

GROUP_ACCOUNTS = [
    {
        "id": 11,
        "email": "group-a@outlook.com",
        "status": "active",
        "group_id": 2,
        "group_name": "注册组",
        "group_color": "#123456",
        "remark": "A",
        "provider": "outlook",
        "pool_status": "available",
        "last_refresh_at": "2026-04-10T10:10:00+00:00",
    },
    {
        "id": 12,
        "email": "group-b@outlook.com",
        "status": "inactive",
        "group_id": 2,
        "group_name": "注册组",
        "group_color": "#123456",
        "remark": "B",
        "provider": "outlook",
        "pool_status": "retired",
        "last_refresh_at": "2026-04-10T10:20:00+00:00",
    },
]


def mock_read_account_messages(account, folder="inbox", **kwargs):
    messages = {
        "inbox": {
            "id": "msg-inbox",
            "date": "2026-04-10T09:00:00+00:00",
            "subject": "Inbox verification code",
        },
        "junkemail": {
            "id": "msg-junk",
            "date": "2026-04-10T10:00:00+00:00",
            "subject": "Junk verification code",
        },
    }
    return {
        "success": True,
        "method": "mock",
        "emails": [messages[folder]],
    }


def mock_read_account_message_detail(account, message_id, folder="inbox"):
    details = {
        "msg-inbox": {
            "id": "msg-inbox",
            "subject": "Inbox verification code",
            "content": "Your verification code is 111111.",
            "html_content": "",
            "from_address": "sender@example.com",
            "timestamp": "2026-04-10T09:00:00+00:00",
            "method": "mock",
        },
        "msg-junk": {
            "id": "msg-junk",
            "subject": "Junk verification code",
            "content": "Your verification code is 654321.",
            "html_content": "",
            "from_address": "sender@example.com",
            "timestamp": "2026-04-10T10:00:00+00:00",
            "method": "mock",
        },
    }
    return {
        "success": True,
        "email": details[message_id],
    }


def mock_read_account_messages_latest_not_code(account, folder="inbox", **kwargs):
    messages = {
        "inbox": [
            {
                "id": "msg-latest-no-code",
                "date": "2026-04-10T10:30:00+00:00",
                "subject": "Security alert",
            },
            {
                "id": "msg-older-with-code",
                "date": "2026-04-10T10:00:00+00:00",
                "subject": "Your verification code",
            },
        ],
        "junkemail": [],
    }
    return {
        "success": True,
        "method": "mock",
        "emails": messages[folder],
    }


def mock_read_account_message_detail_latest_not_code(account, message_id, folder="inbox"):
    details = {
        "msg-latest-no-code": {
            "id": "msg-latest-no-code",
            "subject": "Security alert",
            "content": "There was a login attempt from a new device.",
            "html_content": "",
            "from_address": "security@example.com",
            "timestamp": "2026-04-10T10:30:00+00:00",
            "method": "mock",
        },
        "msg-older-with-code": {
            "id": "msg-older-with-code",
            "subject": "Your verification code",
            "content": "Your verification code is 123456.",
            "html_content": "",
            "from_address": "sender@example.com",
            "timestamp": "2026-04-10T10:00:00+00:00",
            "method": "mock",
        },
    }
    return {
        "success": True,
        "email": details[message_id],
    }


def mock_get_emails_imap_generic(email_addr, imap_password, imap_host, imap_port=993, folder="inbox", provider="custom", skip=0, top=20, proxy_url=""):
    messages = {
        "inbox": {
            "id": "imap-inbox",
            "date": "2026-04-10T09:00:00+00:00",
            "subject": "IMAP inbox verification code",
            "body_preview": "Inbox code 111111",
        },
        "junkemail": {
            "id": "imap-junk",
            "date": "2026-04-10T10:00:00+00:00",
            "subject": "IMAP junk verification code",
            "body_preview": "Junk code 654321",
        },
    }
    return {
        "success": True,
        "emails": [messages[folder]],
        "method": "IMAP (Generic)",
        "has_more": False,
    }


def mock_get_email_detail_imap_generic_result(email_addr, imap_password, imap_host, imap_port=993, message_id="", folder="inbox", provider="custom", proxy_url=""):
    details = {
        "imap-inbox": {
            "id": "imap-inbox",
            "subject": "IMAP inbox verification code",
            "body": "Your verification code is 111111.",
            "body_type": "text",
            "from": "sender@example.com",
            "date": "2026-04-10T09:00:00+00:00",
        },
        "imap-junk": {
            "id": "imap-junk",
            "subject": "IMAP junk verification code",
            "body": "Your verification code is 654321.",
            "body_type": "text",
            "from": "sender@example.com",
            "date": "2026-04-10T10:00:00+00:00",
        },
    }
    return {
        "success": True,
        "email": details[message_id],
    }


def mock_get_emails_imap_with_server(account, client_id, refresh_token, folder="inbox", skip=0, top=20, server="", proxy_url=None, fallback_proxy_urls=None):
    messages = {
        "inbox": {
            "id": "oauth-imap-inbox",
            "date": "2026-04-10T09:00:00+00:00",
            "subject": "OAuth IMAP inbox verification code",
            "body_preview": "Inbox code 777777",
        },
        "junkemail": {
            "id": "oauth-imap-junk",
            "date": "2026-04-10T10:00:00+00:00",
            "subject": "OAuth IMAP junk verification code",
            "body_preview": "Junk code 888888",
        },
    }
    return {
        "success": True,
        "emails": [messages[folder]],
        "method": "IMAP (OAuth)",
        "has_more": False,
    }


def mock_get_email_detail_imap(account, client_id, refresh_token, message_id, folder="inbox", proxy_url=None, fallback_proxy_urls=None):
    details = {
        "oauth-imap-inbox": {
            "id": "oauth-imap-inbox",
            "subject": "OAuth IMAP inbox verification code",
            "from": "sender@example.com",
            "to": "oauth-imap-user@outlook.com",
            "cc": "",
            "date": "2026-04-10T09:00:00+00:00",
            "body": "Your verification code is 777777.",
        },
        "oauth-imap-junk": {
            "id": "oauth-imap-junk",
            "subject": "OAuth IMAP junk verification code",
            "from": "sender@example.com",
            "to": "oauth-imap-user@outlook.com",
            "cc": "",
            "date": "2026-04-10T10:00:00+00:00",
            "body": "Your verification code is 888888.",
        },
    }
    return details[message_id]


class LatestVerificationCodeTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    @patch.object(app_module, "get_account_by_id", return_value=ACTIVE_ACCOUNT)
    @patch.object(app_module, "read_account_messages", side_effect=mock_read_account_messages)
    @patch.object(app_module, "read_account_message_detail", side_effect=mock_read_account_message_detail)
    def test_internal_route_prefers_newer_junk_message(
        self,
        _mock_detail,
        _mock_messages,
        _mock_account,
    ):
        with self.client.session_transaction() as session:
            session["logged_in"] = True

        response = self.client.get("/api/accounts/1/latest-verification-code")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["code"], "654321")
        self.assertEqual(payload["data"]["selected_folder"], "junkemail")
        self.assertEqual(payload["data"]["candidates"][0]["folder"], "junkemail")

    @patch.object(app_module, "get_account_by_id", return_value=IMAP_ACCOUNT)
    @patch.object(app_module, "get_emails_imap_generic", side_effect=mock_get_emails_imap_generic)
    @patch.object(app_module, "get_email_detail_imap_generic_result", side_effect=mock_get_email_detail_imap_generic_result)
    @patch.object(app_module, "read_account_messages", side_effect=AssertionError("read_account_messages should not be used for IMAP OTP accounts"))
    @patch.object(app_module, "read_account_message_detail", side_effect=AssertionError("read_account_message_detail should not be used for IMAP OTP accounts"))
    def test_internal_route_uses_imap_first_for_imap_account(
        self,
        _mock_detail_router,
        _mock_messages_router,
        _mock_imap_detail,
        _mock_imap_messages,
        _mock_account,
    ):
        with self.client.session_transaction() as session:
            session["logged_in"] = True

        response = self.client.get("/api/accounts/3/latest-verification-code")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["code"], "654321")
        self.assertEqual(payload["data"]["selected_folder"], "junkemail")

    @patch.object(app_module, "get_account_by_id", return_value=OAUTH_IMAP_ACCOUNT)
    @patch.object(app_module, "get_emails_imap_with_server", side_effect=mock_get_emails_imap_with_server)
    @patch.object(app_module, "get_email_detail_imap", side_effect=mock_get_email_detail_imap)
    @patch.object(app_module, "get_emails_imap_generic", side_effect=AssertionError("get_emails_imap_generic should not be used for Outlook OAuth IMAP accounts"))
    @patch.object(app_module, "get_email_detail_imap_generic_result", side_effect=AssertionError("get_email_detail_imap_generic_result should not be used for Outlook OAuth IMAP accounts"))
    @patch.object(app_module, "read_account_messages", side_effect=AssertionError("read_account_messages should not be used for IMAP OTP accounts"))
    @patch.object(app_module, "read_account_message_detail", side_effect=AssertionError("read_account_message_detail should not be used for IMAP OTP accounts"))
    def test_internal_route_uses_oauth_imap_for_outlook_imap_account(
        self,
        _mock_detail_router,
        _mock_messages_router,
        _mock_generic_detail,
        _mock_generic_messages,
        _mock_oauth_detail,
        _mock_oauth_messages,
        _mock_account,
    ):
        with self.client.session_transaction() as session:
            session["logged_in"] = True

        response = self.client.get("/api/accounts/4/latest-verification-code")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["code"], "888888")
        self.assertEqual(payload["data"]["selected_folder"], "junkemail")

    @patch.object(app_module, "get_external_api_key", return_value="test-key")
    @patch.object(app_module, "get_account_by_email", return_value=ACTIVE_ACCOUNT)
    @patch.object(app_module, "get_emails_imap_generic", side_effect=AssertionError("get_emails_imap_generic should not be used for Graph accounts"))
    @patch.object(app_module, "get_email_detail_imap_generic_result", side_effect=AssertionError("get_email_detail_imap_generic_result should not be used for Graph accounts"))
    @patch.object(app_module, "read_account_messages", side_effect=mock_read_account_messages)
    @patch.object(app_module, "read_account_message_detail", side_effect=mock_read_account_message_detail)
    def test_external_route_keeps_graph_path_for_non_imap_account(
        self,
        _mock_detail,
        _mock_messages,
        _mock_imap_detail,
        _mock_imap_messages,
        _mock_account,
        _mock_api_key,
    ):
        response = self.client.get(
            "/api/external/verification-code?email=user@outlook.com",
            headers={"X-API-Key": "test-key"},
        )

        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["code"], "654321")
        self.assertEqual(payload["data"]["selected_folder"], "junkemail")

    def test_external_verification_code_uses_same_latest_message_logic_without_default_lookback(self):
        since_minutes_seen = []

        def tracking_messages(account, folder="inbox", **kwargs):
            since_minutes_seen.append((folder, kwargs.get("since_minutes")))
            return mock_read_account_messages(account, folder=folder, **kwargs)

        with patch.object(app_module, "get_external_api_key", return_value="test-key"), \
             patch.object(app_module, "get_account_by_email", return_value=ACTIVE_ACCOUNT), \
             patch.object(app_module, "read_account_messages", side_effect=tracking_messages), \
             patch.object(app_module, "read_account_message_detail", side_effect=mock_read_account_message_detail):
            response = self.client.get(
                "/api/external/verification-code?email=user@outlook.com",
                headers={"X-API-Key": "test-key"},
            )

        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["code"], "654321")
        self.assertEqual(payload["data"]["selected_folder"], "junkemail")
        self.assertEqual(since_minutes_seen, [("inbox", None), ("junkemail", None)])

    def test_external_verification_code_only_uses_newest_of_inbox_and_junk(self):
        with patch.object(app_module, "get_external_api_key", return_value="test-key"), \
             patch.object(app_module, "get_account_by_email", return_value=ACTIVE_ACCOUNT), \
             patch.object(app_module, "read_account_messages", side_effect=mock_read_account_messages_latest_not_code), \
             patch.object(app_module, "read_account_message_detail", side_effect=mock_read_account_message_detail_latest_not_code):
            response = self.client.get(
                "/api/external/verification-code?email=user@outlook.com",
                headers={"X-API-Key": "test-key"},
            )

        payload = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"], "未提取到验证码")

    def test_external_pool_groups_returns_group_detail_with_accounts(self):
        with patch.object(app_module, "get_external_api_key", return_value="test-key"), \
             patch.object(app_module, "is_pool_external_enabled", return_value=True), \
             patch.object(app_module, "get_group_by_id", return_value=GROUP_RECORD), \
             patch.object(app_module, "get_group_account_count", return_value=2), \
             patch.object(app_module, "get_group_pool_counts", return_value={
                 "available": 1,
                 "claimed": 0,
                 "used": 0,
                 "cooldown": 0,
                 "frozen": 0,
                 "retired": 1,
             }), \
             patch.object(app_module, "load_accounts", return_value=GROUP_ACCOUNTS):
            response = self.client.get(
                "/api/external/pool/groups?group_id=2",
                headers={"X-API-Key": "test-key"},
            )

        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["group"]["group_id"], 2)
        self.assertEqual(payload["data"]["group"]["account_count"], 2)
        self.assertEqual(len(payload["data"]["group"]["accounts"]), 2)
        self.assertEqual(payload["data"]["group"]["accounts"][0]["email"], "group-a@outlook.com")
        self.assertEqual(payload["data"]["group"]["accounts"][1]["pool_status"], "retired")

    def test_external_pool_groups_returns_group_summaries_without_accounts_by_default(self):
        with patch.object(app_module, "get_external_api_key", return_value="test-key"), \
             patch.object(app_module, "is_pool_external_enabled", return_value=True), \
             patch.object(app_module, "load_groups", return_value=[GROUP_RECORD]), \
             patch.object(app_module, "get_group_account_count", return_value=2), \
             patch.object(app_module, "get_group_pool_counts", return_value={
                 "available": 1,
                 "claimed": 0,
                 "used": 0,
                 "cooldown": 0,
                 "frozen": 0,
                 "retired": 1,
             }):
            response = self.client.get(
                "/api/external/pool/groups",
                headers={"X-API-Key": "test-key"},
            )

        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(len(payload["data"]["groups"]), 1)
        self.assertEqual(payload["data"]["groups"][0]["group_id"], 2)
        self.assertNotIn("accounts", payload["data"]["groups"][0])


class RefreshAccountStatusTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        app_module.app.config["WTF_CSRF_ENABLED"] = False
        self.client = app_module.app.test_client()

        with app_module.app.app_context():
            db = app_module.get_db()
            db.execute("DELETE FROM account_refresh_logs")
            db.execute("DELETE FROM accounts")
            db.commit()

    def _insert_outlook_account(self, email_prefix, status="active", account_type="outlook"):
        email = f"{email_prefix}-{uuid.uuid4().hex[:8]}@example.com"
        with app_module.app.app_context():
            db = app_module.get_db()
            encrypted_refresh_token = app_module.encrypt_data("refresh-token-for-test")
            encrypted_password = app_module.encrypt_data("password-for-test")
            db.execute(
                """
                INSERT INTO accounts (
                    email, password, client_id, refresh_token, group_id,
                    remark, status, account_type, provider,
                    imap_host, imap_port, imap_password, forward_enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    email,
                    encrypted_password,
                    "test-client-id",
                    encrypted_refresh_token,
                    1,
                    "",
                    status,
                    account_type,
                    "outlook" if account_type == "outlook" else "custom",
                    "outlook.live.com" if account_type == "outlook" else "imap.example.com",
                    993,
                    "",
                    0,
                ),
            )
            db.commit()
            row = db.execute("SELECT id, email FROM accounts WHERE email = ?", (email,)).fetchone()
            return row["id"], row["email"]

    def test_log_refresh_result_disables_failed_and_reactivates_success(self):
        account_id, email = self._insert_outlook_account("refresh-status")

        with app_module.app.app_context():
            app_module.log_refresh_result(account_id, email, "manual", "failed", "token invalid")
            db = app_module.get_db()
            row = db.execute("SELECT status FROM accounts WHERE id = ?", (account_id,)).fetchone()
            self.assertEqual(row["status"], "inactive")

            app_module.log_refresh_result(account_id, email, "manual", "success", None)
            row = db.execute("SELECT status, last_refresh_at FROM accounts WHERE id = ?", (account_id,)).fetchone()
            self.assertEqual(row["status"], "active")
            self.assertIsNotNone(row["last_refresh_at"])

    def test_load_refresh_target_accounts_includes_failed_inactive_accounts(self):
        active_id, _ = self._insert_outlook_account("active-outlook", status="active", account_type="outlook")
        inactive_failed_id, inactive_failed_email = self._insert_outlook_account("inactive-failed", status="inactive", account_type="outlook")
        inactive_nonfailed_id, inactive_nonfailed_email = self._insert_outlook_account("inactive-ok", status="inactive", account_type="outlook")
        imap_active_id, _ = self._insert_outlook_account("imap-active", status="active", account_type="imap")

        with app_module.app.app_context():
            db = app_module.get_db()
            db.execute(
                "INSERT INTO account_refresh_logs (account_id, account_email, refresh_type, status, error_message) VALUES (?, ?, ?, ?, ?)",
                (inactive_failed_id, inactive_failed_email, "manual", "failed", "x"),
            )
            db.execute(
                "INSERT INTO account_refresh_logs (account_id, account_email, refresh_type, status, error_message) VALUES (?, ?, ?, ?, ?)",
                (inactive_nonfailed_id, inactive_nonfailed_email, "manual", "success", None),
            )
            db.commit()

            targets = app_module.load_refresh_target_accounts(db)
            target_ids = {row["id"] for row in targets}

            self.assertIn(active_id, target_ids)
            self.assertIn(inactive_failed_id, target_ids)
            self.assertNotIn(inactive_nonfailed_id, target_ids)
            self.assertNotIn(imap_active_id, target_ids)

    def test_refresh_failed_api_reactivates_inactive_account_on_success(self):
        account_id, email = self._insert_outlook_account("retry-inactive", status="inactive", account_type="outlook")

        with app_module.app.app_context():
            db = app_module.get_db()
            db.execute(
                "INSERT INTO account_refresh_logs (account_id, account_email, refresh_type, status, error_message) VALUES (?, ?, ?, ?, ?)",
                (account_id, email, "manual", "failed", "token expired"),
            )
            db.commit()

        with patch.object(app_module, "test_refresh_token", return_value=(True, None)):
            with self.client.session_transaction() as session:
                session["logged_in"] = True

            response = self.client.post("/api/accounts/refresh-failed")
            payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["success_count"], 1)
        self.assertEqual(payload["failed_count"], 0)

        with app_module.app.app_context():
            db = app_module.get_db()
            row = db.execute("SELECT status FROM accounts WHERE id = ?", (account_id,)).fetchone()
            self.assertEqual(row["status"], "active")


if __name__ == "__main__":
    unittest.main()
