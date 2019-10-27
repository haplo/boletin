.. contents::

=============================================
Boletin, a Django newsletter app (deprecated)
=============================================

**Boletin is DEPRECATED, it hasn't been updated in a long time and is not expected to currently work**.

Boletin is a generic newsletter application for Django projects, which allows
for automatically generating and sending newsletters, with optional human
reviewing process if so desired.

Boletin means "bulletin" or "newsletter" in Spanish.


Features
========

 * Complete subscription/desubscription process, with confirmation emails.

 * Completely decoupled, no need to modify your own code to use it, only
   ``settings.py`` and redefine templates as needed.

 * Newsletters in HTML and plain text in the same email.

 * Three different periods: daily, weekly and monthly newsletters, easily
   configurable.

 * Integrated with Django's admin.

 * Optional reviewing process (in the admin).

 * Cron scripts included.

 * Unit tests included.


Installation
============

 1. Include ``boletin`` in ``settings.INSTALLED_APPS``.

 2. Create DB tables with ``python manage.py syncdb``.

 3. Configure settings (see `Configuration`_ section).

 4. Install cron scripts in the system's cron installation for automated
    newsletter creation and (optionally) automated sending.
    See "Cron configuration" below for more information.


Configuration
=============

You can configure many aspects of the behavior of the application via
settings variables. Mandatory variables are marked with (*).


NEWSLETTER_EMAIL (*)
--------------------

Email address from where to send the newsletter. Newsletter recipients
will see this address in the e-mail message "From" field.

Default: None, it's mandatory.

Example::

    NEWSLETTER_EMAIL = 'newsletter@example.com'


NEWSLETTER_REVIEWER_EMAIL
-------------------------

Email address for the newsletter reviewer. When a newsletter is generated,
an e-mail will be sent to this address prompting to the revision of the
newsletter.

Default: None.

Example::

    NEWSLETTER_REVIEWER_EMAIL = 'reviewer@example.com'


NEWSLETTER_REVIEWER_ADMIN_LINK
------------------------------

Relative URL suffix for newsletter objects in the admin application. The site
domain and the newsletter id will be, respectively, prepended and appended to
this string. This setting is optional; if not defined, the e-mail message to
the reviewer will not include a link to the admin application.

Default: None.

Example::

    NEWSLETTER_REVIEWER_ADMIN_LINK = '/admin/boletin/newsletter/'

NEWSLETTER_GENERATOR_FUNCTION (*)
---------------------------------

This variable is a string pointing to a function inside the project which
will be responsible for retrieving content for inclusion in each newsletter.

The function must receive two parameters: ``from_date`` and ``to_date``, which define
the datetime range of the newsletter being created.

Default: None, it's mandatory.

Example::

    NEWSLETTER_GENERATOR_FUNCTION = 'portal.newsletter.generate_content'

And the content of portal/newsletter.py::

    from app1.models import FooModel
    from app2.models import BarModel

    def generate_content(from_date, to_date):
        app1 = FooModel.objects.filter(date__gte=from_date, date__lte=to_date)
        app2 = BarModel.objects.filter(date__gte=from_date, date__lte=to_date)
        return {'app1': app1, 'app2': app2}


NEWSLETTER_PERIODS
------------------
Available newsletter periods in the project. It's a list with one or more of
'D' (daily), 'W' (weekly) and 'M' (monthly).

Default: ``['W']`` (only weekly newsletter)

Example::

    NEWSLETTER_PERIODS = ['D', 'W', 'M'] # daily, weekly and monthly newsletters


Management commands
===================

Three management commands are included:

 * ``createnewsletter``

 * ``sendnewsletter``

 * ``shownewsletter``

Createnewsletter
----------------

Generate a new newsletter for the given period (daily, weekly or monthly), both
in HTML and plain text. It renders the `templates`_ ``newsletter_email.html``
and ``newsletter_email.txt``.

Options:

 * ``-d``, ``--daily``: daily period.

 * ``-w``, ``--weekly``: weekly period.

 * ``-m``, ``--monthly``: monthly period.

 * ``-p``, ``--print``: print the created newsletter to stdout.

 * ``-r``, ``--regenerate``: create the newsletter again if it already exists.

One and only one of ``-d``, ``-w`` or ``-m`` must be given.

Sendnewsletter
--------------

Send newsletters to subscribers.

Options:

 * ``-n``, ``--newsletter``: send only the newsletter with the given ID.

 * ``-f``, ``--force-unreviewed``: send unreviewed newsletters.

Without parameters all **reviewed** newsletters with pending sendings are
sent. Use the ``-f`` switch to send unreviewed newsletters (useful for a
completely automatic newsletter system). Use the ``-n`` switch to send an
specific newsletter. The `shownewsletters`_ command should be useful to see
created newsletters, their IDs and pending statuses.

Shownewsletters
---------------

Show stored newsletters, with their object ID (*different than their newsletter
number*) and pending status.

Options:

 * ``-p``, ``--only-pending``: show only newsletters with pending sendings.

Templates
=========

Default templates are provided for the subscription and unsubscription process,
but you should redefine at least ``newsletter_email.txt`` and
``newsletter_email.html``.  You can redefine any template creating a newsletter
dir inside your templates directory, copying the app template inside it and
changing that copy.

The available templates are:

    * ``newsletter_base.html``: base template for the subscription and
      unsubscription process, except email templates.

    * ``newsletter_confirm_email.txt``: email template for confirming subscription.

    * ``newsletter_confirm.html``: page telling the user the subscription
      confirmation email has been sent to her email address.

    * ``newsletter_email.html``: email template of a newsletter in HTML format.
      You should redefine this depending on the context returned by the
      ``NEWSLETTER_GENERATOR_FUNCTION``.

    * ``newsletter_email.txt``: same as newsletter_email.html, but in plain text.

    * ``newsletter.html``: subscription/unsubscription form.

    * ``newsletter_success.html``: subscription success page.

    * ``newsletter_unsubscription_confirm_email.txt``: same as
      newsletter_confirm_email, but for unsubscription.

    * ``newsletter_unsubscription_confirm.html``: same as newsletter_confirm,
      but for unsubscription.

    * ``newsletter_unsubscription_success.html``: same as newsletter_success,
      but for unsubscription.

Cron configuration
==================

There are several crontab files inside the ``cron`` directory that you can
simply include in your system-wide cron configuration to have automatic
newsletter creation and/or sending. The ``createnewsletter`` and
``sendnewsletter`` commands are smart enough to ignore petitions for unallowed
periods (i.e. not configured in `NEWSLETTER_PERIODS`_).

Development
===========

You can get the last bleeding edge version of boletin by doing a checkout of
trunk in its subversion repository::

  svn checkout https://svnpub.yaco.es/djangoapps/boletin/trunk boletin

Bug reports, patches and suggestions are more than welcome. Just put
them in our Trac system and use the 'boletin' component when you fill
tickets::

  https://tracpub.yaco.es/djangoapps/
