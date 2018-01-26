from datetime import timedelta
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from hc.api.models import Check, Ping


class PingTestCase(TestCase):

    def setUp(self):
        super(PingTestCase, self).setUp()
        self.check = Check.objects.create()

    def test_it_works(self):
        r = self.client.get("/ping/%s/" % self.check.code)
        assert r.status_code == 200

        self.check.refresh_from_db()
        assert self.check.status == "up"

        ping = Ping.objects.latest("id")
        assert ping.scheme == "http"

    def test_it_handles_bad_uuid(self):
        r = self.client.get("/ping/not-uuid/")
        assert r.status_code == 400

    def test_it_handles_120_char_ua(self):
        ua = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/44.0.2403.89 Safari/537.36")

        r = self.client.get("/ping/%s/" % self.check.code, HTTP_USER_AGENT=ua)
        assert r.status_code == 200

        ping = Ping.objects.latest("id")
        assert ping.ua == ua

    def test_it_truncates_long_ua(self):
        ua = "01234567890" * 30

        r = self.client.get("/ping/%s/" % self.check.code, HTTP_USER_AGENT=ua)
        assert r.status_code == 200

        ping = Ping.objects.latest("id")
        assert len(ping.ua) == 200
        assert ua.startswith(ping.ua)

    def test_it_reads_forwarded_ip(self):
        ip = "1.1.1.1"
        r = self.client.get("/ping/%s/" % self.check.code,
                            HTTP_X_FORWARDED_FOR=ip)
        ping = Ping.objects.latest("id")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(ping.remote_addr, ip)
        ### Assert the expected response status code and ping's remote address

        ip = "1.1.1.1, 2.2.2.2"
        r = self.client.get("/ping/%s/" % self.check.code,
                            HTTP_X_FORWARDED_FOR=ip, REMOTE_ADDR="3.3.3.3")
        ping = Ping.objects.latest("id")
        assert r.status_code == 200
        assert ping.remote_addr == "1.1.1.1"

    def test_it_reads_forwarded_protocol(self):
        r = self.client.get("/ping/%s/" % self.check.code,
                            HTTP_X_FORWARDED_PROTO="https")
        ping = Ping.objects.latest("id")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(ping.scheme, 'https')
        ### Assert the expected response status code and ping's scheme

    def test_it_never_caches(self):
        r = self.client.get("/ping/%s/" % self.check.code)
        assert "no-cache" in r.get("Cache-Control")

    ### Test that a post to a ping works
    def test_it_works_with_post(self):
        """
        This tests a post to ping works
        """
        response = self.client.post(reverse("hc-ping", args=[self.check.code]))
        assert response.status_code == 200

        self.check.refresh_from_db()
        assert self.check.status == "up"

        ping = Ping.objects.latest("id")
        assert ping.scheme == "http"

    ### Test that when a ping is made a check with a paused status changes status
    def test_it_changes_paused_check_to_up(self):
        """
        This test ensures that when a ping is made a check with a paused status
        changes status to up
        """
        self.check.status = 'paused'
        self.check.save()
        self.client.get(reverse("hc-ping", args=[self.check.code]))
        self.check.refresh_from_db()
        self.assertEqual(self.check.status, 'up')

    ### Test that the csrf_client head works
    def test_that_the_csrf_head_works(self):
        """
        This test asserts that the csrf_client works
        """
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.head(reverse("hc-ping", args=[self.check.code]))
        self.assertEqual(response.status_code, 200)

    # Test that a check that runs too often is flagged
    def test_it_flags_checks_that_run_too_often(self):
        """Checks should not run too often"""
        # Create test check
        test_check = Check.objects.create()
        # Ping check to change it's status to "UP"
        response = self.client.get(
            reverse("hc-ping", args=[test_check.code])
        )
        self.assertEqual(response.status_code, 200)
        test_check.refresh_from_db()
        # Ping check to change trigger often state
        response = self.client.get(
            reverse("hc-ping", args=[test_check.code])
        )
        self.assertEqual(response.status_code, 200)
        test_check.refresh_from_db()
        self.assertEqual(test_check.status, "up")
        self.assertEqual(test_check.often, True)
        # Assert that is check is ran after the reverse grace "Often" reverts to "False".
        reverse_grace = test_check.timeout - test_check.grace
        # set the last ping to an appropriate time after the reverse grace but before the
        # timeout
        test_check.last_ping = timezone.now() - reverse_grace - timedelta(minutes=30)
        test_check.save()
        response = self.client.get(
            reverse("hc-ping", args=[test_check.code])
        )
        test_check.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        # Assert that the check is still up
        self.assertEqual(test_check.status, "up")
        # Assert that the often property is now False
        self.assertEqual(test_check.often, False)
