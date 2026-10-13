import unittest
from datetime import datetime
from unittest.mock import Mock, patch
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
import litellm_lan_auth_proxy as proxy


class ScheduleTests(unittest.TestCase):
    def test_boundaries_weekdays_weekends_and_dst(self):
        cases = [
            ("2026-10-12T12:59:59+00:00", False),
            ("2026-10-12T13:00:00+00:00", True),
            ("2026-10-16T21:59:59+00:00", True),
            ("2026-10-16T22:00:00+00:00", False),
            ("2026-10-17T15:00:00+00:00", False),
            ("2026-10-18T15:00:00+00:00", False),
            ("2026-11-02T13:59:59+00:00", False),
            ("2026-11-02T14:00:00+00:00", True),
            ("2026-11-02T23:00:00+00:00", False),
            ("2027-03-15T12:59:59+00:00", False),
            ("2027-03-15T13:00:00+00:00", True),
        ]
        for stamp, expected in cases:
            with self.subTest(stamp=stamp):
                now = datetime.fromisoformat(stamp)
                self.assertEqual(proxy.is_scheduled_block("192.168.86.2", now), expected)
                self.assertFalse(proxy.is_scheduled_block("192.168.86.3", now))


class MiddlewareTests(unittest.IsolatedAsyncioTestCase):
    async def test_socket_peer_and_forwarded_header_spoofing(self):
        async def accepted(request):
            return web.Response(status=204)
        for path in ("/v1/models", "/v1/chat/completions", "/metrics"):
            for peer, forwarded, blocked, expected in [
                ("192.168.86.2", "192.168.86.3", True, 403),
                ("192.168.86.3", "192.168.86.2", True, 204),
                ("192.168.86.2", "192.168.86.2", False, 204),
            ]:
                transport = Mock()
                request = make_mocked_request("GET", path, headers={"X-Forwarded-For": forwarded}, transport=transport)
                request.transport.get_extra_info.return_value = (peer, 12345)
                with patch.object(proxy, "is_scheduled_block", side_effect=lambda ip: blocked and ip == proxy.BLOCKED_IP):
                    response = await proxy.scheduled_ip_block(request, accepted)
                self.assertEqual(response.status, expected)

if __name__ == "__main__":
    unittest.main()