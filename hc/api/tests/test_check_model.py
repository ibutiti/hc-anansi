from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from hc.api.models import Check


class CheckModelTestCase(TestCase):

    def test_it_strips_tags(self):
        check = Check()

        check.tags = " foo  bar "
        self.assertEqual(check.tags_list(), ["foo", "bar"])
        # Repeat above test for when check is an empty string

    def test_check_empty_string(self):
        check = Check()
        # pass an empty string into tags attribute
        check.tags = ""

        # the check.tags_list splits strings into a list, space as a delimitter
        # an empty string should therefore yield an empty list
        self.assertEqual(check.tags_list(), [])

    def test_status_works_with_grace_period(self):
        # create a new check instance
        check = Check()

        # set its status to up as new checks default to status new
        check.status = "up"

        # set last ping to 1day 30min ago
        # default timeout is 1 day, default grace period is 1hr thus check
        # is within grace period
        check.last_ping = timezone.now() - timedelta(days=1, minutes=30)

        self.assertTrue(check.in_grace_period())
        self.assertEqual(check.get_status(), "up")

        # The above 2 asserts fail. Make them pass
        # Test passes and is correct, check falls outside grace period after
        # 1 day and 1 hour. Here check still within grace period

    def test_paused_check_is_not_in_grace_period(self):
        # create a new check
        check = Check()

        # since new checks default to status new, change status to up
        check.status = "up"
        # set last ping to 1day 30min ago, still in grace period as default
        # timeout and grace period sum to 1day 1 hour
        check.last_ping = timezone.now() - timedelta(days=1, minutes=30)

        # verify check in grace period
        self.assertTrue(check.in_grace_period())
        # change check status to paused and test if in grace period
        # in_grace_period method should yield false
        check.status = "paused"
        self.assertFalse(check.in_grace_period())

    def test_new_check_not_in_grace_period(self):
        # create a new check, should default to status new
        check = Check()

        # use in_grace_period method to verify new check is not in grace period
        self.assertFalse(check.in_grace_period())

    # Test that when a new check is created, it is not in the grace period
