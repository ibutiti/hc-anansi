from django.urls import reverse
from hc.api.models import Check
from hc.test import BaseTestCase


class AddCheckTestCase(BaseTestCase):

    def test_it_works(self):
        url = "/checks/add/"
        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(url)
        self.assertRedirects(r, "/checks/")
        assert Check.objects.count() == 1

    ### Test that team access works
    def test_team_access_works(self):
        # Login in with Bob to confirm that that he doesn't have any checks.
        self.client.login(username="bob@example.org", password="password")
        self.client.get(reverse('hc-checks'))
        assert Check.objects.count() == 0
        self.client.logout()

        # Login with Alice and add a new check then logout.
        self.client.login(username="alice@example.org", password="password")
        url = reverse('hc-add-check')
        response = self.client.post(url)
        self.client.logout()

        # Login with bob and check if he can see the new check in alice's team.
        self.client.login(username="bob@example.org", password="password")
        self.assertRedirects(response, reverse('hc-checks'))
        assert Check.objects.count() == 1
