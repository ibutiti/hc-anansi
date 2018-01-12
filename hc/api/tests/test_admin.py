from hc.api.models import Channel, Check
from hc.test import BaseTestCase


class ApiAdminTestCase(BaseTestCase):

    def setUp(self):
        super(ApiAdminTestCase, self).setUp()
        self.check = Check.objects.create(user=self.alice, tags="foo bar")

        # access the user instance through the check object and set
        # its attributes using django built in methods and save
        self.check.user.is_superuser = True
        self.check.user.is_staff = True
        self.check.user.save()
        # Set Alice to be staff and superuser and save her :)

    def test_it_shows_channel_list_with_pushbullet(self):
        # login with user alice
        self.client.login(username="alice@example.org", password="password")

        # create channel object for alice with pushbullet as kind and save
        ch = Channel(user=self.alice, kind="pushbullet", value="test-token")
        ch.save()
        # refresh check object with db values
        ch.refresh_from_db()

        # assert that the kind attribute is pushbullet
        self.assertEqual(ch.kind, 'pushbullet')
        # Assert for the push bullet
        # make comments on code for readability and flow
