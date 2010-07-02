# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from boletin.models import PERIOD, NewsletterSubscription


class NewsletterSubscriptionForm(forms.Form):
    email = forms.EmailField(_(u'Email'), required=True)
    period = forms.ChoiceField(label=_(u'Periodicity'), choices=PERIOD,
        widget=forms.RadioSelect, initial='W')
    unsubscribe = forms.BooleanField(label=u'', required=False,
        help_text=_(u'If you wish to unsubscribe check this box'))

    default_error_messages = {
        'not_subscribed': _(u'This email address is not subscribed to the newsletter.'),
        'subscribed': _(u'This email address is already subscribed to the newsletter.'),
    }

    def __init__(self, *args, **kwargs):
        super(NewsletterSubscriptionForm, self).__init__(*args, **kwargs)
        periods = [(code, name) for code, name in PERIOD
                                if code in settings.NEWSLETTER_PERIODS]
        self.fields['period'].choices = periods
        if self.fields['period'].initial not in settings.NEWSLETTER_PERIODS:
            self.fields['period'].initial = None

    def clean_email(self):
        if 'email' in self.cleaned_data:
            if 'unsubscribe' in self.data:
                if not NewsletterSubscription.objects.filter(email=self.cleaned_data['email']):
                    raise forms.ValidationError(self.default_error_messages['not_subscribed'])
            else:
                if NewsletterSubscription.objects.filter(email=self.cleaned_data['email']):
                    raise forms.ValidationError(self.default_error_messages['subscribed'])
        return self.cleaned_data.get('email', None)
