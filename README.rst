.. image:: https://github.com/jgosmann/doveseed/actions/workflows/ci.yml/badge.svg
  :target: https://github.com/jgosmann/doveseed/actions/workflows/ci.yml
  :alt: CI and release pipeline
.. image:: https://codecov.io/gh/jgosmann/doveseed/branch/main/graph/badge.svg
  :target: https://codecov.io/gh/jgosmann/doveseed
  :alt: Codecov coverage
.. image:: https://img.shields.io/pypi/v/doveseed
  :target: https://pypi.org/project/doveseed/
  :alt: PyPI
.. image:: https://img.shields.io/pypi/pyversions/doveseed
  :target: https://pypi.org/project/doveseed/
  :alt: PyPI - Python Version
.. image:: https://img.shields.io/pypi/l/doveseed
  :target: https://pypi.org/project/doveseed/
  :alt: PyPI - License

.. image:: https://github.com/jgosmann/doveseed/blob/main/doveseed-logo.png
  :alt: Doveseed logo
  :width: 145


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
  * ``port``: SMTP port used to send notification emails (defaul: ``0`` = auto-select).
  * ``user``: SMTP logon user name.
  * ``password``: SMTP logon password.
  * ``ssl_mode``: Activate/deactivate SSL/TLS, valid values ``"no-ssl"``, ``"start-tls"``, ``"tls"`` (default ``"start-tls"``).
  * ``check_hostname``: Whether to verify the hostname when using TLS (default ``true``).

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
* ``confirm_timeout_minutes``: Timeout in minutes during which a subscription needs to be confirmed.

**Ensure that the configuration files have appropriate permissions, i.e. only
readable by you and Doveseed.**

By default the configuration filename is assumed to be ``config.json``.


Email templates
^^^^^^^^^^^^^^^

Templates for the emails sent out are written in
`Jinja <https://jinja.palletsprojects.com/en/2.11.x/>`_.
Look in ``templates/example`` for example email templates.
There is a template for each type of email being sent:

* ``new-post.*``: for notifications about new posts,
* ``subscribe.*``: for requesting confirmation to a new subscription,
* and ``unsubscribe.*``: for requesting confirmation to a cancellation of a subscription.

Each of these templates consists out of three files:

* ``*.subject.txt``: for the subject line of the email,
* ``*.txt``: for the plain text version of the email,
* and ``*.html``: for the HTML version of the email.



REST service
^^^^^^^^^^^^

The REST service runs as a Python `ASGI app
<https://asgi.readthedocs.io/en/latest/>`_. See the FastAPI documentation for
`deployment options <https://fastapi.tiangolo.com/deployment/>`_.



CORS
~~~~

To set appropriate CORS headers use the `FastAPI CORSMiddleware
<https://fastapi.tiangolo.com/tutorial/cors/>`_. Activate it by adding the
following lines to the file where you instantiate the app::

    from doveseed.app import app
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://example.com"],
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization"],
    )


ReCaptcha
~~~~~~~~~

You activate `ReCaptcha (v2) <https://www.google.com/recaptcha/>`_ verification of
requests with Doveseed.

First, you need to install the required optional dependencies::

    pip install 'doveseed[recaptcha]'

Then, add the follwing lines to the file where you instantiate the app::

    from doveseed.app import app
    from doveseed.recaptcha import ReCaptchaMiddleware

    app.add_middleware = ReCaptchaMiddleware('^/(un)?subscribe/.*', 'recaptcha.json')

Also, create the ``recaptcha.json`` with the required ReCaptcha configuration:

* ``hostnames``: List of hostnames to accept ReCaptchas from.
* ``secret``: The shared key between your site and reCAPTCHA.


**Ensure that the configuration files have appropriate permissions, i.e. only
readable by you and Doveseed.**


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


REST interface
--------------

Health
^^^^^^

To check the service health:

    GET /health

Returns a 204 (no content) status if the service is up and running.

Subscribe
^^^^^^^^^

To subscribe with an email address::

    POST /subscribe/<url encoded email>
    Content-Type: application/json

    { captcha: "ReCaptcha returned from Google API" }

This will return a ``201 NO CONTENT`` and send out the email requesting
confirmation.

Unsubscribe
^^^^^^^^^^^

To unsubscribe an email address::

    POST /unsubscribe/<url encoded email>
    Content-Type: application/json

    { captcha: "ReCaptcha returned from Google API" }

This will return a ``201 NO CONTENT`` and send out the email requesting
confirmation if the email is subscribed.

Confirm
^^^^^^^

To confirm a request to subscribe or unsubscribe::

    POST /confirm/<url encoded email>
    Content-Type: application/json
    Authorization: Bearer <token from confirmation reuest email>

This will return a ``201 NO CONTENT`` on success,
and ``401 UNAUTHORIZED`` if the token or email is invalid.
