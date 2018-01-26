from django import forms
from hc.api.models import Channel
from pagedown.widgets import PagedownWidget


class NameTagsForm(forms.Form):
    name = forms.CharField(max_length=100, required=False)
    tags = forms.CharField(max_length=500, required=False)

    def clean_tags(self):
        l = []

        for part in self.cleaned_data["tags"].split(" "):
            part = part.strip()
            if part != "":
                l.append(part)

        return " ".join(l)


#increase max value in forms to allow upto 60days
#increase max value in forms to allow upto 60days
class TimeoutForm(forms.Form):
    min_time = 60
    max_time = 5184000
    timeout = forms.IntegerField(min_value=min_time, max_value=max_time)
    grace = forms.IntegerField(min_value=min_time, max_value=max_time)
    nag = forms.IntegerField(min_value=min_time, max_value=max_time)


class PriorityForm(forms.Form):
    """Form to accept check priority and escalation emails"""
    escalation_emails = forms.CharField(max_length=500, required=False)
    priority = forms.IntegerField(min_value=-2, max_value=2)


class AddChannelForm(forms.ModelForm):

    class Meta:
        model = Channel
        fields = ['kind', 'value']

    def clean_value(self):
        value = self.cleaned_data["value"]
        return value.strip()


class AddWebhookForm(forms.Form):
    error_css_class = "has-error"

    value_down = forms.URLField(max_length=1000, required=False)
    value_up = forms.URLField(max_length=1000, required=False)

    def get_value(self):
        return "{value_down}\n{value_up}".format(**self.cleaned_data)

class CreateBlogPost(forms.Form):
    content = forms.CharField(widget = PagedownWidget)

class CreateCategory(forms.Form):
    category = forms.CharField(widget = forms.TextInput(attrs = {
        'class':'form-control',
        'placeholder':'category name'
           }))

class CreateCommentForm(forms.Form):
    comment = forms.CharField(widget = forms.TextInput(attrs = {
        'class':'form-control',
        'placeholder':'category name'
           }))
