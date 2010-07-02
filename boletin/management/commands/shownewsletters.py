# -*- coding: utf-8 -*-
from optparse import make_option

from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--only-pending', '-p', default=False, dest='only_pending',
            action='store_true', help="Show only newsletters with pending sendings."),
    )
    help = u"Show newsletters."

    def handle_noargs(self, **options):
        from boletin.models import Newsletter, PERIOD

        only_pending = options.get('only_pending')

        if only_pending:
            newsletters = Newsletter.objects.get_pending()
        else:
            newsletters = Newsletter.objects.all()

        for period_code, period_name in PERIOD:
            print u"%s newsletters" % period_name
            for newsletter in newsletters.filter(period=period_code):
                pending_string = newsletter.is_pending() and '(*) ' or '    '
                print "%s%3d. Newsletter #%s" % (pending_string, newsletter.id, newsletter.number)
            print
