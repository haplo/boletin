# -*- coding: utf-8 -*-
import calendar
from cStringIO import StringIO
from datetime import date, timedelta
import random
import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command, CommandError
from django.template.defaultfilters import linebreaksbr
from django.test import TestCase, Client

from boletin.management.commands.createnewsletter import Command as CreateNewsletter
from boletin.models import Newsletter, NewsletterSubscription


class MangleTemplateTestCase(TestCase):
    """This TestCase if to be used as a parent class for tests that use
    'app.urls' and therefore need to define their own base.html template,
    because the project's base.html includes references to views defined
    in the project's ROOTURL.

    """

    def setUp(self):
        self.old_template_loaders = settings.TEMPLATE_LOADERS[:] # make copy
        self.mangle_template_loaders()

    def tearDown(self):
        settings.TEMPLATE_LOADERS = self.old_template_loaders

    def mangle_template_loaders(self):
        """Give priority to the app template loader to override the base
        template and avoid url reverse errors."""
        template_loaders = list(settings.TEMPLATE_LOADERS)
        app_template_loader = 'django.template.loaders.app_directories.load_template_source'
        if app_template_loader in template_loaders:
            template_loaders.remove(app_template_loader)
        template_loaders.insert(0, app_template_loader)
        settings.TEMPLATE_LOADERS = template_loaders


class NewsletterSubscriptionTests(MangleTemplateTestCase):
    """Newsletter subscription and unsubscription are accesible to all
    users, even unregistered ones, it only requires a working email account.

    Both subscription and unsubscription send a confirmation email.

    """
    urls = 'boletin.tests_urls'

    def setUp(self):
        MangleTemplateTestCase.setUp(self)
        random.seed(42) # confirmation keys are random
        User.objects.create_user(username='test_user',
                                 email='test_user@host.net',
                                 password='tester')

    def testSubscription(self):
        """Anyone can subscribe to the newsletter just giving an email."""
        c = Client()
        # subscription form
        response = c.get('/subscribe/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, '<input id="id_email" type="text"')
        # subscription form sends a confirmation email
        # and creates an unconfirmed NewsletterSubscription
        response = c.post('/subscribe/', {'email': 'test_user@host.net',
                                          'period': 'W'})
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'boletin/newsletter_success.html')
        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue('test_user@host.net' in mail.outbox[0].recipients())
        confirmation_url = '/subscribe/confirm/rnTP3fAbnFbmOHnKYaXRvj7uff0LYT/'
        self.assertTrue(confirmation_url in mail.outbox[0].body)
        subscription = NewsletterSubscription.objects.get(email='test_user@host.net')
        self.assertEquals(subscription.period, 'W')
        self.assertEquals(subscription.hashkey, 'rnTP3fAbnFbmOHnKYaXRvj7uff0LYT')
        self.assertEquals(subscription.confirmed, False)
        # the user confirms the subscription
        response = c.get(confirmation_url)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'boletin/newsletter_confirm.html')
        subscription = NewsletterSubscription.objects.get(email='test_user@host.net')
        self.assertEquals(subscription.confirmed, True)

    def testRegisteredUserEmailAutocompletion(self):
        """Registered users have the email field automatically filled in"""
        c = Client()
        c.login(username='test_user', password='tester')
        response = c.get('/subscribe/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, '<input id="id_email" type="text"')
        self.assertContains(response, 'value="test_user@host.net"')

    def testUnsubscription(self):
        c = Client()
        NewsletterSubscription.objects.create(email='test_user@host.net',
                                              period='M',
                                              confirmed='True')
        # request newsletter unsubscription
        response = c.post('/subscribe/', {'email': 'test_user@host.net',
                                          'period': 'W',
                                          'unsubscribe': True})
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'boletin/newsletter_unsubscription_success.html')
        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue('test_user@host.net' in mail.outbox[0].recipients())
        confirmation_url = '/unsubscribe/confirm/H8xIZM1JRcoreogrNwwmq6OLkTkx9N/'
        self.assertTrue(confirmation_url in mail.outbox[0].body)
        subscription = NewsletterSubscription.objects.get(email='test_user@host.net')
        self.assertEquals(subscription.period, 'M')
        self.assertEquals(subscription.hashkey, 'H8xIZM1JRcoreogrNwwmq6OLkTkx9N')
        self.assertEquals(subscription.confirmed, True)
        # the user confirms the unsubscription and it's deleted from DB
        response = c.get(confirmation_url)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'boletin/newsletter_unsubscription_confirm.html')
        self.assertRaises(NewsletterSubscription.DoesNotExist,
                          NewsletterSubscription.objects.get, email='test_user@host.net')


class NewsletterCommandTestCase(MangleTemplateTestCase):
    """Base TestCase class for the testing of newsletter commands.

    """

    def setUp(self):
        MangleTemplateTestCase.setUp(self)

    def executeCommand(self, command, *args, **kwargs):
        stdout = sys.stdout
        sys.stdout = output = StringIO()
        call_command(command, *args, **kwargs)
        sys.stdout = stdout
        return linebreaksbr(output.getvalue())


def generate_content(from_date, to_date):
    objects = NewsletterSubscription.objects.filter(
        subscription_date__gte=from_date,
        subscription_date__lte=to_date,
    )
    return {'objects': objects}


class CreateNewsletterCommandTests(NewsletterCommandTestCase):
    """Test the createnewsletter command for the automatic generation of
    newsletters.

    """

    def setUp(self):
        NewsletterCommandTestCase.setUp(self)
        self.obj = NewsletterSubscription.objects.create(
            email='test_user@host.net', period='M', confirmed='True')
        settings.NEWSLETTER_GENERATOR_FUNCTION = 'boletin.tests.generate_content'

    def testCreateNewsletterBadArgs(self):
        """createnewsletter without parameters should fail requiring a period.

        It should also fail if two or more periods are provided.
        """
        # can't use call_command because CommandError is raised and
        # the test would fail
        self.assertRaises(CommandError, CreateNewsletter().handle)
        self.assertRaises(CommandError, CreateNewsletter().handle,
                          daily=True, weekly=True)
        self.assertRaises(CommandError, CreateNewsletter().handle,
                          daily=True, monthly=True)
        self.assertRaises(CommandError, CreateNewsletter().handle,
                          weekly=True, monthly=True)
        self.assertRaises(CommandError, CreateNewsletter().handle,
                          daily=True, weekly=True, monthly=True)

    def testCreateNewsletterDaily(self):
        """createnewsletter --daily."""
        output = self.executeCommand('createnewsletter', daily=True)
        self.assertTrue('No content, no newsletter.' in output)
        self.obj.subscription_date = self.obj.subscription_date-timedelta(days=1)
        self.obj.save()
        output = self.executeCommand('createnewsletter', daily=True)
        Newsletter.objects.get(number=1, period='D')

    def testCreateNewsletterWeekly(self):
        """createnewsletter --weekly."""
        output = self.executeCommand('createnewsletter', weekly=True)
        self.assertTrue('No content, no newsletter.' in output)
        self.obj.subscription_date = self.obj.subscription_date-timedelta(days=7)
        self.obj.save()
        output = self.executeCommand('createnewsletter', weekly=True)
        Newsletter.objects.get(number=1, period='W')

    def testCreateNewsletterMonthly(self):
        """createnewsletter --monthly."""
        output = self.executeCommand('createnewsletter', monthly=True)
        self.assertTrue('No content, no newsletter.' in output)
        weekday, days = calendar.monthrange(self.obj.subscription_date.year,
                                            self.obj.subscription_date.month)
        self.obj.subscription_date = self.obj.subscription_date-timedelta(days=days)
        self.obj.save()
        output = self.executeCommand('createnewsletter', monthly=True)
        Newsletter.objects.get(number=1, period='M')

    def testCreateNewsletterPrint(self):
        """createnewsletter --regenerate."""
        self.obj.subscription_date = self.obj.subscription_date-timedelta(days=7)
        self.obj.save()
        output = self.executeCommand('createnewsletter', **{'weekly': True, 'print': True})
        self.assertTrue('Newsletter #1' in output)
        self.assertTrue('test_user@host.net' in output)

    def testCreateNewsletterRegenerate(self):
        """createnewsletter --regenerate."""
        self.obj.subscription_date = self.obj.subscription_date-timedelta(days=7)
        self.obj.save()
        output = self.executeCommand('createnewsletter', weekly=True)
        output = self.executeCommand('createnewsletter', weekly=True)
        self.assertTrue('Already generated' in output)
        self.obj.email = 'another_user@another_host.org'
        self.obj.save()
        output = self.executeCommand('createnewsletter', weekly=True, regenerate=True)
        newsletter = Newsletter.objects.get(number=1, period='W')
        self.assertTrue('another_user@another_host.org' in newsletter.text_content)
        self.assertTrue('another_user@another_host.org' in newsletter.html_content)

    def testCreateNewsletterWithReviewer(self):
        """Test if createnewsletter sends an email to the reviewer
        if settings.NEWSLETTER_REVIEWER_EMAIL is set."""
        settings.NEWSLETTER_REVIEWER_EMAIL = 'reviewer@host'
        settings.NEWSLETTER_REVIEWER_ADMIN_LINK = '/admin/boletin/'
        self.obj.subscription_date = self.obj.subscription_date-timedelta(days=7)
        self.obj.save()
        output = self.executeCommand('createnewsletter', weekly=True)
        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue('reviewer@host' in mail.outbox[0].recipients())
        self.assertTrue('/admin/boletin/' in mail.outbox[0].body)


class SendNewsletterCommandTests(NewsletterCommandTestCase):
    """Test the sendnewsletter command, responsible for sending pending
    newsletters to subscribers.

    """

    def setUp(self):
        NewsletterCommandTestCase.setUp(self)
        # avoid problem with subscription_date by
        # creating the subscriptions before than the newsletters
        NewsletterSubscription.objects.create(email='user1@host',
                                              period='D',
                                              confirmed=True)
        NewsletterSubscription.objects.create(email='user2@host',
                                              period='D',
                                              confirmed=False)
        NewsletterSubscription.objects.create(email='user3@host',
                                              period='W',
                                              confirmed=True)
        NewsletterSubscription.objects.create(email='user4@host',
                                              period='W',
                                              confirmed=False)
        NewsletterSubscription.objects.create(email='user5@host',
                                              period='M',
                                              confirmed=True)
        NewsletterSubscription.objects.create(email='user6@host',
                                              period='M',
                                              confirmed=False)
        Newsletter.objects.create(number=1, period='D',
                                  date=date(2009, 2, 2),
                                  text_content='Test daily',
                                  html_content='Test daily',
                                  reviewed=True)
        Newsletter.objects.create(number=2, period='D',
                                  date=date(2008, 2, 14),
                                  text_content='Test daily',
                                  html_content='Test daily',
                                  reviewed=True,
                                  pending=False)
        Newsletter.objects.create(number=1, period='W',
                                  date=date(2008, 5, 25),
                                  text_content='Test weekly',
                                  html_content='Test weekly',
                                  reviewed=False)
        Newsletter.objects.create(number=1, period='M',
                                  date=date(2009, 3, 8),
                                  text_content='Test monthly',
                                  html_content='Test monthly',
                                  reviewed=True)

    def testSendNewsletter(self):
        """sendnewsletter without arguments, sends all pending newsletters to
        the corresponding subscribers."""
        output = self.executeCommand('sendnewsletter')
        self.assertTrue('Sending daily newsletter #1 to 1 subscribers' in output)
        self.assertTrue('Sending monthly newsletter #1 to 1 subscribers' in output)
        self.assertEquals(len(mail.outbox), 2)
        self.assertTrue('user1@host' in mail.outbox[0].recipients())
        self.assertTrue('Test daily' in mail.outbox[0].body)
        self.assertTrue('user5@host' in mail.outbox[1].recipients())
        self.assertTrue('Test monthly' in mail.outbox[1].body)
        output = self.executeCommand('sendnewsletter')
        self.assertTrue('No newsletters to send' in output)

    def testSendNewsletterOnlyOne(self):
        """sendnewsletter --newsletter=N."""
        output = self.executeCommand('sendnewsletter', newsletter=1)
        self.assertTrue('Sending daily newsletter #1 to 1 subscribers' in output)
        self.assertFalse('Sending monthly newsletter #1 to 1 subscribers' in output)
        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue('user1@host' in mail.outbox[0].recipients())
        self.assertTrue('Test daily' in mail.outbox[0].body)
        output = self.executeCommand('sendnewsletter', newsletter=1)
        self.assertTrue("This newsletter has already been sent" in output)
        output = self.executeCommand('sendnewsletter', newsletter=3)
        self.assertTrue("This newsletter hasn't been reviewed" in output)

    def testSendNewsletterForceUnreviewed(self):
        """sendnewsletter --force-unreviewed."""
        output = self.executeCommand('sendnewsletter', newsletter=3, unreviewed=True)
        self.assertTrue('Sending weekly newsletter #1 to 1 subscribers' in output)
        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue('user3@host' in mail.outbox[0].recipients())
        self.assertTrue('Test weekly' in mail.outbox[0].body)
        output = self.executeCommand('sendnewsletter', newsletter=3, unreviewed=True)
        self.assertTrue("This newsletter has already been sent" in output)


class ShowNewslettersCommandTests(NewsletterCommandTestCase):
    """Test the shownewsletters command, which shows all generated
    newsletters."""

    def setUp(self):
        NewsletterCommandTestCase.setUp(self)
        Newsletter.objects.create(number=1, period='D',
                                  date=date(2009, 2, 2),
                                  text_content='Test daily',
                                  html_content='Test daily',
                                  pending=True)
        Newsletter.objects.create(number=2, period='D',
                                  date=date(2008, 2, 14),
                                  text_content='Test daily',
                                  html_content='Test daily',
                                  pending=False)
        Newsletter.objects.create(number=1, period='W',
                                  date=date(2008, 5, 25),
                                  text_content='Test weekly',
                                  html_content='Test weekly',
                                  pending=False)
        Newsletter.objects.create(number=1, period='M',
                                  date=date(2009, 3, 8),
                                  text_content='Test monthly',
                                  html_content='Test monthly',
                                  pending=True)

    def testShowNewsletters(self):
        """shownewsletters"""
        output = self.executeCommand('shownewsletters')
        self.assertTrue('Daily newsletters' in output)
        self.assertTrue('Weekly newsletters' in output)
        self.assertTrue('Monthly newsletters' in output)
        self.assertTrue('(*)   1. Newsletter #1' in output)
        self.assertTrue('      2. Newsletter #2' in output)
        self.assertTrue('      3. Newsletter #1' in output)
        self.assertTrue('(*)   4. Newsletter #1' in output)

    def testShowNewslettersOnlyPending(self):
        """shownewsletters --only-pending"""
        output = self.executeCommand('shownewsletters', only_pending=True)
        self.assertTrue('Daily newsletters' in output)
        self.assertTrue('Weekly newsletters' in output)
        self.assertTrue('Monthly newsletters' in output)
        self.assertTrue('(*)   1. Newsletter #1' in output)
        self.assertFalse('2.' in output)
        self.assertFalse('3.' in output)
        self.assertTrue('(*)   4. Newsletter #1' in output)
