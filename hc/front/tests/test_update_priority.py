from hc.api.models import Check
from hc.test import BaseTestCase


class UpdatePriorityTestCase(BaseTestCase):

    def setUp(self):
        super(UpdatePriorityTestCase, self).setUp()
        self.check = Check(user=self.alice)
        self.check.save()

    def test_update_priority_works(self):
        url = "/checks/{}/priority/".format(self.check.code)
        user_email = "alice@example.com"
        payload = {"priority": 2, "escalation_email": user_email}

        self.client.login(username="alice@example.org", password="password")
        r = self.client.post(url, data=payload)
        self.assertRedirects(r, "/checks/")

        check = Check.objects.get(code=self.check.code)

        assert check.priority == 2
        assert check.escalation_email == user_email
