from django.test.utils import override_settings
from django.urls import reverse

from hc.api.models import Channel
from hc.test import BaseTestCase


@override_settings(PUSHOVER_API_TOKEN="token", PUSHOVER_SUBSCRIPTION_URL="url")
class AddChannelTestCase(BaseTestCase):

    def test_it_adds_email(self):
        url = "/integrations/add/"
        form = {"kind": "email", "value": "alice@example.org"}

        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(url, form)

        self.assertRedirects(r, "/integrations/")
        assert Channel.objects.count() == 1

    def test_it_trims_whitespace(self):
        """ Leading and trailing whitespace should get trimmed. """

        url = "/integrations/add/"
        form = {"kind": "email", "value": "   alice@example.org   "}

        self.client.login(username="alice@example.org", password="password")
        self.client.post(url, form)

        q = Channel.objects.filter(value="alice@example.org")
        self.assertEqual(q.count(), 1)

    def test_instructions_work(self):
        self.client.login(username="alice@example.org", password="password")
        kinds = ("email", "webhook", "pd", "pushover", "hipchat", "victorops")
        for kind in kinds:
            url = reverse('hc-add-%s'%kind)
            response = self.client.get(url)
            self.assertContains(response, "Integration Settings", status_code=200)

    ### Test that the team access works
    def test_teamaccess_works(self):

        url = reverse('hc-add-channel')
        form = {"kind": "email", "value": "alice@example.com"}

        self.client.login(username="alice@example.org", password="password")
        self.client.post(url, form)
        alice_channels = Channel.objects.filter(user=self.alice)
        self.client.logout()

        self.client.login(username="bob@example.org", password="password")
        response = self.client.get(reverse('hc-channels'))
        self.assertContains(response, alice_channels.first().code)
        self.assertEquals(response.status_code, 200)


    ### Test that bad kinds don't work
    def test_bad_kinds_dont_work(self):
        # Bad kinds means that a user can't add unsupported intergrations.
        self.client.login(username="alice@example.org")
        bad_kind = "whatsapp"
        url = "/integrations/add_%s" % bad_kind
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
