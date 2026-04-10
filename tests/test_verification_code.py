import os
import sys
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
