from datetime import timedelta
import time

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from hc.accounts.models import Profile
from hc.api.models import Check


def num_pinged_checks(profile):
    q = Check.objects.filter(user_id=profile.user.id,)
    q = q.filter(last_ping__isnull=False)
    return q.count()


class Command(BaseCommand):
    help = 'Send due monthly reports'
    tmpl = "Sending monthly report to %s"

    def add_arguments(self, parser):
        parser.add_argument(
            '--loop',
            action='store_true',
            dest='loop',
            default=False,
            help='Keep running indefinitely in a 300 second wait loop',
        )

    def handle_one_run(self):
        now = timezone.now()
        report_due = Q(next_report_date__lt=now)
        report_not_scheduled = Q(next_report_date__isnull=True)

        q = Profile.objects.filter(report_due | report_not_scheduled)
        q = q.filter(~Q(reports_allowed='none'))

        sent = 0

        for profile in q:
            if(profile.next_report_date == ""):
                days = 0
                if profile.reports_allowed == 'Daily':
                    days = 1
                elif profile.reports_allowed == 'Weekly':
                    days = 7
                elif profile.reports_allowed == 'Monthly':
                    days = 30
                else:
                    break
                period_before = now - timedelta(days=days)
                if profile.user.date_joined > period_before:
                    break

            if num_pinged_checks(profile) > 0:
                self.stdout.write(self.tmpl % profile.user.email)
                profile.send_report()
                sent += 1

        return sent

    def handle(self, *args, **options):
        if not options["loop"]:
            return "Sent %d reports" % self.handle_one_run()

        self.stdout.write("sendreports is now running")
        while True:
            self.handle_one_run()

            formatted = timezone.now().isoformat()
            self.stdout.write("-- MARK %s --" % formatted)

            time.sleep(300)
