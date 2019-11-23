Doveseed
========

Doveseed is a backend service for email subscriptions to RSS feeds.


Setup
-----

Configuration
^^^^^^^^^^^^^

Doveseed requires a configuration file in JSON format. Take a look at
``config.sample.json``. The format is as follows:

* ``db``: JSON file in which Doveseed persists its data.
* ``rss``: URL to the RSS feed for which new notifications are to be send.
* ``smtp``

  * ``host``: SMTP host used to send notification emails.
  * ``user``: SMTP logon user name.
  * ``password``: SMTP logon password.

* ``template_vars``: Defines template variables to replace in the email templates.

  * ``display_name``: Name for the website to use in emails.
  * ``host``: Hostname of the website.
  * ``sender``: Email address that is sending the notifications.
  * ``confirm_url_format``: Template for the URL that is used for confirmation
    links. The following values will be replaced in it:

    * ``{host}`` with the specified host,
    * ``{email}`` with the email address to confirm,
    * ``{token}`` with the confirmation token,
    * ``{{`` and ``}}`` with ``{`` and ``}``.

* ``email_templates``: Path to the templates for the emails.

**Ensure that the configuration files has appropriate permissions, i.e. only
readable by you and Doveseed.**

By default the configuration filename is assumed to be ``config.json``.


REST service
^^^^^^^^^^^^

The REST service runs as a Python WSGI app. Any WSGI app server could be used.

Passenger
~~~~~~~~~

Sample ``passenger_wsgi.py`` file::

    import logging
    logging.basicConfig(filename="/path/to/log", level=logging.WARN)

    from doveseed.app import create_app
    application = create_app()


CORS
~~~~

TODO


ReCaptcha
~~~~~~~~~


Database cleanup
^^^^^^^^^^^^^^^^

Expired pending subscription can be cleaned from the database with::

    python -m doveseed.cli clean <path to config file>

Ideally, this command is run once per day as a cron job.


Checking for new posts
^^^^^^^^^^^^^^^^^^^^^^

To check for new post and send notification emails run::

    python -m doveseed.cli notify <path to config file>

This can either run in a regular interval as a cron job or it can be triggered
in some way after new posts have been published.

**Run this command once to initialize the database before going live because
initially all items in the RSS feed will be considered to be old.** (This
prevents sending a notification email for all already existing items in the
feed.)


Usage of the REST interface
---------------------------

TODO


Email templates
---------------

TODO
