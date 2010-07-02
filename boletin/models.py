# -*- coding: utf-8 -*-
import random
import string

from django.db import models
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _

DAILY = 'D'
WEEKLY = 'W'
MONTHLY = 'M'

PERIOD = (
    (DAILY, _(u'Daily')),
    (WEEKLY, _(u'Weekly')),
    (MONTHLY, _(u'Monthly')),
)


class NewsletterManager(models.Manager):

    def get_pending(self):
        return self.get_query_set().filter(pending=True)


class Newsletter(models.Model):
    """A newsletter with HTML and plain text content.

    Newsletters' numbers are unique in each period, and are generated
    automatically.

    >>> import datetime
    >>> newsletter = Newsletter.objects.create(period='W', text_content='Test',
    ...                                        html_content='<p>Test</p>',
    ...                                        date=datetime.date(2009, 2, 2))
    >>> newsletter.number
    1
    >>> newsletter = Newsletter.objects.create(period='W', text_content='Test',
    ...                                        html_content='<p>Test</p>',
    ...                                        date=datetime.date(2009, 5, 25))
    >>> newsletter.number
    2
    >>> newsletter = Newsletter.objects.create(period='D', text_content='Test',
    ...                                        html_content='<p>Test</p>',
    ...                                        date=datetime.date(2009, 4, 2))
    >>> newsletter.number
    1

    """
    number = models.PositiveIntegerField(_(u'number'))
    period = models.CharField(_(u'periodicity'), choices=PERIOD, max_length=1)
    text_content = models.TextField(_(u'text content'))
    html_content = models.TextField(_(u'html content'))
    date_created = models.DateTimeField(_(u'date created'), auto_now_add=True)
    date = models.DateField(_(u'first day'))
    reviewed = models.BooleanField(_('reviewed?'), default=False)
    pending = models.BooleanField(_('pending sendings?'), default=True)

    objects = NewsletterManager()

    class Meta:
        ordering= ('date', )
        get_latest_by = 'date_created'
        unique_together = (('number', 'period'), )
        verbose_name = _(u'newsletter')
        verbose_name_plural = _(u'newsletters')

    def __unicode__(self):
        if len(self.text_content) > 50:
            return '%s...' % self.text_content[:47]
        else:
            return self.text_content

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = Newsletter.next_number(self.period)
        super(Newsletter, self).save(*args, **kwargs)

    @classmethod
    def next_number(cls, period):
        """Compute the number for the next newsletter."""
        try:
            number = cls._default_manager.filter(period=period).values('number').order_by('-number')[0]['number']+1
        except IndexError:
            number = 1
        return number

    def is_pending(self):
        return self.pending


class NewsletterSubscriptionManager(models.Manager):

    def get_pending_sendings(self, newsletter=None):
        if newsletter is None:
            newsletter = Newsletter.objects.latest()
        return self.get_query_set().filter(period=newsletter.period,
                                           confirmed=True,
                                           subscription_date__lte=newsletter.date_created,
                                          ).exclude(newslettersending__newsletter=newsletter)


class NewsletterSubscription(models.Model):
    '''Subscription to the portal newsletter.'''
    email = models.EmailField(_(u'email'), unique=True)
    period = models.CharField(_(u'periodicity'), choices=PERIOD, max_length=1)
    subscription_date = models.DateTimeField(_(u'subscription date'), auto_now_add=True)
    hashkey = models.CharField(_(u'hash key'), max_length=100)
    confirmed = models.BooleanField(_(u'confirmed'), default=False)

    objects = NewsletterSubscriptionManager()

    class Meta:
        ordering= ('email', )
        verbose_name = _(u'newsletter subscription')
        verbose_name_plural = _(u'newsletter subscriptions')

    def __unicode__(self):
        return ugettext('Newsletter subscription for %(email)s') % {'email': self.email}

    def save(self, *args, **kwargs):
        if not self.hashkey:
            self.hashkey = self.random_key()
        super(NewsletterSubscription, self).save(*args, **kwargs)

    def random_key(self):
        alphabet = [c for c in string.letters + string.digits if ord(c) < 128]
        return ''.join([random.choice(alphabet) for x in xrange(30)])


class NewsletterSending(models.Model):
    '''A subscriber-level newsletter sending.'''
    newsletter = models.ForeignKey(Newsletter, verbose_name=_(u'newsletter'))
    subscription = models.ForeignKey(NewsletterSubscription, verbose_name=_(u'subscription'))
    date = models.DateTimeField(_(u'date and time of sending'), auto_now_add=True)
