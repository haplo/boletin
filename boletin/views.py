# -*- coding: utf-8 -*-
import sys
from cStringIO import StringIO

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core import management
from django.forms.util import ErrorList
from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, Context, RequestContext
from django.template.defaultfilters import linebreaks
from django.utils.translation import ugettext as _

from boletin.forms import NewsletterSubscriptionForm
from boletin.models import Newsletter, NewsletterSubscription


def newsletter_subscription(request):
    if request.method == 'POST':
        form = NewsletterSubscriptionForm(data=request.POST.copy())
        if form.is_valid():
            email = form.cleaned_data.get('email')
            period = form.cleaned_data.get('period')
            unsubscribe = form.cleaned_data.get('unsubscribe')
            current_site = Site.objects.get_current()
            if unsubscribe:
                subscription = get_object_or_404(NewsletterSubscription, email=email)
                subscription.hashkey = subscription.random_key()
                subscription.save()
                t = loader.get_template('boletin/newsletter_unsubscription_confirm_email.txt')
                c = Context({'key': subscription.hashkey, 'site': current_site})
                send_mail(u'[%s] %s' % (current_site.name, _(u'Newsletter unsubscription confirmation')),
                          t.render(c), settings.NEWSLETTER_EMAIL, [email], fail_silently=False)
                return render_to_response('boletin/newsletter_unsubscription_success.html',
                                          {'email': email},
                                          context_instance=RequestContext(request))
            else:
                subscription = NewsletterSubscription.objects.create(email=email, period=period)
                t = loader.get_template('boletin/newsletter_confirm_email.txt')
                c = Context({'key': subscription.hashkey, 'site': current_site})
                send_mail(u'[%s] %s' % (current_site.name, _(u'Newsletter subscription confirmation')),
                          t.render(c), settings.NEWSLETTER_EMAIL, [email], fail_silently=False)
                return render_to_response('boletin/newsletter_success.html',
                                        {'email': email},
                                        context_instance=RequestContext(request))
    else:
        if request.user.is_authenticated():
            initial = {'email': request.user.email}
        else:
            initial = {}
        form = NewsletterSubscriptionForm(initial=initial)
    return render_to_response('boletin/newsletter.html',
                              {'form': form},
                              context_instance=RequestContext(request))


def newsletter_subscription_confirm(request, key):
    subscription = get_object_or_404(NewsletterSubscription, hashkey=key)
    error = ''
    if subscription.confirmed:
        error = ErrorList([_('This subscription has already been confirmed.')])
    else:
        subscription.confirmed = True
        subscription.hashkey = u''
        subscription.save()
    return render_to_response('boletin/newsletter_confirm.html',
                              {'subscription': subscription, 'error': error},
                              context_instance=RequestContext(request))


def newsletter_unsubscription_confirm(request, key):
    subscription = get_object_or_404(NewsletterSubscription, hashkey=key)
    email = subscription.email
    subscription.delete()
    return render_to_response('boletin/newsletter_unsubscription_confirm.html',
                              {'email': email},
                              context_instance=RequestContext(request))


def newsletter_send(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    stdout = sys.stdout
    sys.stdout = output = StringIO()
    management.call_command('sendnewsletter', newsletter=newsletter.id)
    sys.stdout = stdout

    title_data = {'number': newsletter.number,
                  'period': newsletter.get_period_display()}
    title = u'%(period)s newsletter #%(number)s sending results' % title_data

    return render_to_response('admin/boletin/newsletter/newsletter_send.html',
                              {'content': linebreaks(output.getvalue()),
                               'title': title,
                               'newsletter': newsletter,
                               'app_label': Newsletter._meta.app_label,
                               'model_name': Newsletter._meta.verbose_name_plural,
                              },
                              context_instance=RequestContext(request))
