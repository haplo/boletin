from django.conf.urls.defaults import *

urlpatterns = patterns('boletin.views',
    (r'^subscribe/$', 'newsletter_subscription'),
    (r'^subscribe/confirm/(?P<key>\w+)/$', 'newsletter_subscription_confirm'),
    (r'^unsubscribe/confirm/(?P<key>\w+)/$', 'newsletter_unsubscription_confirm'),
)
