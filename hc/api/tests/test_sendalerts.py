from datetime import timedelta

from django.utils import timezone
from hc.api.management.commands.sendalerts import Command
from hc.api.models import Check
from hc.test import BaseTestCase
from mock import patch


class SendAlertsTestCase(BaseTestCase):

    @patch("hc.api.management.commands.sendalerts.Command.handle_one")
    def test_it_handles_few(self, mock):
        yesterday = timezone.now() - timedelta(days=1)
        names = ["Check %d" % d for d in range(0, 10)]

        for name in names:
            check = Check(user=self.alice, name=name)
            check.alert_after = yesterday
            check.status = "up"
            check.save()

        result = Command().handle_many()
        assert result, "handle_many should return True"

        handled_names = []
        for args, kwargs in mock.call_args_list:
            handled_names.append(args[0].name)

        assert set(names) == set(handled_names)
        ### The above assert fails. Make it pass

    @patch("hc.api.management.commands.sendalerts.Command.handle_one")
    def test_it_handles_grace_period(self, mock):
        check = Check(user=self.alice, status="up")
        # 1 day 30 minutes after ping the check is in grace period:
        check.last_ping = timezone.now() - timedelta(days=1, minutes=30)
        check.save()

        # Expect no exceptions--
        Command().handle_one(check)

    ## Assert when Command's handle many that when handle_many should return True
    @patch("hc.api.management.commands.sendalerts.Command.handle_one")
    def test_it_only_returns_true_when_handling_many(self, mock):
        """
        This test ensures that only the Command's handle many will return True when
        handling many checks
        """
        # Assest that it returns False when handling one
        # create single check
        check = Check(user=self.alice, status="up")

        # Set the check a day and after the initial ping it will be in the grace period
        check.last_ping = timezone.now() - timedelta(days=1, minutes=45)
        check.save()

        # Assert that result is false
        result = Command().handle_many()
        self.assertFalse(result)

        # Create a list of checks
        names = ["Check %d" % i for i in range(1, 26)]
        # Set the time which each check will alert after
        overdue = timezone.now() - timedelta(days=1)

        # Initialize the checks list with names and the overdue alert_after
        for name in names:
            check = Check(user=self.alice, name=name, status="up")
            check.alert_after = overdue
            check.save()

        # Assert that result of Command's handle_many is True
        result = Command().handle_many()
        self.assertTrue(result)
