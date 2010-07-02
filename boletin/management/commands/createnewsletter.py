# -*- coding: utf-8 -*-
import datetime
from optparse import make_option

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.management.base import CommandError, NoArgsCommand
from django.template import loader, Context
from django.template.loader import render_to_string


def get_dates(period, today=None):
    """Returns a tuple with two dates defining an interval,
    depending on the periodicity given.

    Daily periodicity spans yesterday, from 00:00:00 to 23:59:59.

    Weekly periodicity spans from previous Monday 00:00:00
    to previous Sunday 23:59:59.

    Monthly periodicity spans from first day of the previous month 00:00:00
    to its last day 23:59:59.
    """
    from boletin.models import DAILY, WEEKLY, MONTHLY

    today = today or datetime.date.today()
    weekday = today.weekday()

    if period == DAILY:
        from_date = datetime.datetime(today.year, today.month, today.day) \
                   -datetime.timedelta(days=1)
        to_date = from_date \
                 +datetime.timedelta(days=1) \
                 -datetime.timedelta(seconds=1)
        period = DAILY
    elif period == WEEKLY:
        from_date = datetime.datetime(today.year, today.month, today.day) \
                   -datetime.timedelta(days=weekday+7)
        to_date = from_date \
                 +datetime.timedelta(days=7) \
                 -datetime.timedelta(seconds=1)
        period = WEEKLY
    elif period == MONTHLY:
        year, month = today.year, today.month
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
        from_date = today.replace(year=year, month=month, day=1)
        to_date = datetime.datetime(today.year, today.month, 1) \
                 -datetime.timedelta(seconds=1)
        period = MONTHLY
    else:
        raise ValueError("Periodicity must be one of '%(DAILY)s', " \
                         "'%(WEEKLY)s' or '%(MONTHLY)s'" % locals())

    return (from_date, to_date)


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--daily', '-d', default=False, dest='daily',
            action='store_true', help='Daily newsletter.'),
        make_option('--weekly', '-w', default=False, dest='weekly',
            action='store_true', help='Weekly newsletter.'),
        make_option('--monthly', '-m', default=False, dest='monthly',
            action='store_true', help='Monthly newsletter.'),
        make_option('--print', '-p', default=False, dest='print',
            action='store_true', help="Print the newsletter."),
        make_option('--regenerate', '-r', default=False, dest='regenerate',
            action='store_true', help="Regenerate newsletter."),
    )
    help = u"Generate newsletter."

    def handle_noargs(self, **options):
        from boletin.models import Newsletter, DAILY, WEEKLY, MONTHLY, PERIOD

        daily = options.get('daily')
        weekly = options.get('weekly')
        monthly = options.get('monthly')
        do_print = options.get('print')
        regenerate = options.get('regenerate')

        if not daily and not weekly and not monthly:
            raise CommandError("Provide one of --daily, --weekly and --monthly.")
        if (daily and weekly) or (weekly and monthly) or (daily and monthly):
            raise CommandError("Use only one of --daily, --weekly and --monthly.")

        if daily:
            period = DAILY
        if weekly:
            period = WEEKLY
        if monthly:
            period = MONTHLY
        period_name = dict(PERIOD)[period]
        from_date, to_date = get_dates(period)

        # generate content
        function = self.import_generator_function()
        content = function(from_date, to_date)
        # sanitize content removing empty values
        content = dict([(k, v) for k, v in content.iteritems() if v])
        if not content:
            print "No content, no newsletter."
            return

        site = Site.objects.get_current()
        # create the newsletter
        old_pending = False
        try:
            newsletter = Newsletter.objects.get(date=from_date, period=period)
            if regenerate:
                old_pending = newsletter.pending
                newsletter.delete()
                raise Newsletter.DoesNotExist
            else:
                print "Already generated."
        except Newsletter.DoesNotExist:
            number = Newsletter.next_number(period)
            email_context = {
                'number': number,
                'period': period_name,
                'from': from_date,
                'to': to_date,
                'site': site,
            }
            email_context.update(content)
            email_context = Context(email_context)
            message_text = loader.get_template('boletin/newsletter_email.txt').render(email_context)
            message_html = loader.get_template('boletin/newsletter_email.html').render(email_context)
            newsletter = Newsletter.objects.create(text_content=message_text,
                                                   html_content=message_html,
                                                   number=number,
                                                   date=from_date,
                                                   period=period,
                                                   pending=old_pending)
            print "Generated %s newsletter #%d" % (newsletter.get_period_display(), newsletter.number)
            if hasattr(settings, 'NEWSLETTER_REVIEWER_EMAIL'):
                if hasattr(settings, 'NEWSLETTER_REVIEWER_ADMIN_LINK'):
                    newsletter_url = settings.NEWSLETTER_REVIEWER_ADMIN_LINK
                else:
                    newsletter_url = None
                body = render_to_string('boletin/reviewer_email.txt',
                                        {'site': site,
                                         'newsletter': newsletter,
                                         'newsletter_url': newsletter_url,
                                        },
                                       )
                send_mail("[%s] Newsletter #%d ready to be reviewed" % (site.name, newsletter.number),
                          body,
                          settings.NEWSLETTER_EMAIL,
                          [settings.NEWSLETTER_REVIEWER_EMAIL, ])
        if do_print:
            print newsletter.text_content

    def import_generator_function(self):
        """HIGH BLACK MAGIC, I'm not proud of this. It imports the generator
        function from settings.NEWSLETTER_GENERATOR_FUNCTION.
        """
        module_path, function_name = settings.NEWSLETTER_GENERATOR_FUNCTION.rsplit('.', 1)
        module = __import__(module_path, {}, {}, [function_name])
        return getattr(module, function_name)
