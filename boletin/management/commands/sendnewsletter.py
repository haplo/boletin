# -*- coding: utf-8 -*-
from optparse import make_option

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, SMTPConnection, mail_admins
from django.core.management.base import CommandError, NoArgsCommand


def send_mail(subject, message_txt, message_html, sender, recipients):
    """Similar to django's send_mass_mail, but use EmailMultiAlternatives
    for email messages.

    Also, avoid creating a list with all the messages, use an iterator instead.
    """
    connection = SMTPConnection(fail_silently=False)

    def messages_iterator():
        for recipient in recipients:
            email = EmailMultiAlternatives(subject, message_txt, sender, recipient)
            email.attach_alternative(message_html, 'text/html')
            yield email
    return connection.send_messages(messages_iterator())


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--newsletter', '-n', default=None, dest='newsletter', type='int',
            help='Send the newsletter with the given ID.'),
        make_option('--force-unreviewed', '-f', default=False, dest='unreviewed',
            action='store_true', help='Send unreviewed newsletters.'),
    )
    help = u"Send newsletter to subscribers."

    def handle_noargs(self, **options):
        from boletin.models import (Newsletter, NewsletterSubscription,
                                    NewsletterSending)

        newsletter_id = options.get('newsletter')
        send_unreviewed = options.get('unreviewed')

        newsletters = Newsletter.objects.get_pending()
        if newsletter_id:
            newsletters = newsletters.filter(id=newsletter_id)
        if not send_unreviewed:
            newsletters = newsletters.filter(reviewed=True)

        for newsletter in newsletters:
            subscribers = NewsletterSubscription.objects.get_pending_sendings(newsletter=newsletter)

            # actual sending of emails
            print "Sending %s newsletter #%s to %d subscribers." % (newsletter.get_period_display().lower(),
                                                                    newsletter.number,
                                                                    subscribers.count())
            subject = '[Saludinnova] Boletín de noticias #%d' % newsletter.number
            from_email = settings.NEWSLETTER_EMAIL
            try:
                for subscriber in subscribers:
                    email = EmailMultiAlternatives(subject, newsletter.text_content, from_email, [subscriber.email])
                    email.attach_alternative(newsletter.html_content, 'text/html')
                    email.send()
                    NewsletterSending.objects.create(subscription=subscriber, newsletter=newsletter)
                    print "Sent to &lt;%s&gt;" % subscriber.email
            except Exception, e:
                mail_admins('Error sending newsletter #%s' % newsletter.number, e)
                raise CommandError("Error sending newsletter!")
            else:
                newsletter.pending = False
                newsletter.save()

        if not newsletters:
            if newsletter_id:
                try:
                    newsletter = Newsletter.objects.get(id=newsletter_id)
                except Newsletter.DoesNotExist:
                    raise CommandError("No newsletter by that ID")
                else:
                    if not newsletter.pending:
                        print "This newsletter has already been sent"
                    elif not newsletter.reviewed:
                        print "This newsletter hasn't been reviewed"
            else:
                print "No newsletters to send"
