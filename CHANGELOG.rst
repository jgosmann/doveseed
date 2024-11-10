Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[2.1.2] - 2024-11-10
--------------------

* Enclose content ID within angle brackets in header for better compatibility
  with different email clients.


[2.1.1] - 2024-11-02
--------------------

Fixed
^^^^^

* Make content IDs from ``include_related`` world-unique as required by RFC2387.


[2.1.0] - 2024-11-02
--------------------

Added
^^^^^

* ``include_related`` function within templates that allows for the inclusion
  of files (e.g. images) into the email for inline usage/reference via content
  ID. This can be used to include inline images.


[2.0.5] - 2024-10-27
--------------------

Added
^^^^^

* Official support for Python 3.13.


[2.0.4] - 2024-05-26
--------------------

Security
^^^^^^^^

* Update dependencies to mitigate vulnerabilities:
  - `CVE-2024-30251 <https://nvd.nist.gov/vuln/detail/CVE-2024-30251>`_ (denial of service)
  - `CVE-2024-34064 <https://nvd.nist.gov/vuln/detail/CVE-2024-34064>`_ (Jinja HTML attribute injection, doveseed likely no affected)


[2.0.3] - 2024-02-17
--------------------

Added
^^^^^

* Officially declare Python 3.12 support.
* Tag Docker image of latest stable version with ``latest`` tag.
* Publish Docker image for ``linux/amd64`` and ``linux/arm64`` platforms.

Security
^^^^^^^^

* Update dependencies to mitigate `CVE-2024-24762 <https://nvd.nist.gov/vuln/detail/CVE-2024-24762>`_.


[2.0.2] - 2023-12-03
--------------------

Security
^^^^^^^^

* Update aiohttp to version 3.9.0.

[2.0.1] - 2023-08-09
--------------------

Security
^^^^^^^^

* Update certifi dependency to version 2023.07.22 to mitigate CVE-2023-37920.


[2.0.0] - 2023-04-16
--------------------

Changed
^^^^^^^

* Ported the code from Flask to FastAPI.
* The ``app`` argument was removed from the ``ReCaptchaMiddleware``.

Removed
^^^^^^^

* Support for Python 3.7, 3.8.
* CORS configuration via the configuration JSON file. Use the `FastAPI
  CORSMiddleware <https://fastapi.tiangolo.com/tutorial/cors/>`_ instead.


[1.1.0] - 2023-04-11
--------------------

Added
^^^^^

* Allow connecting to SMTP with SSL (instead of ``START_TLS``) or no encrpytion
  at all. See the ``ssl_mode`` option.
* Allow to configure CORS via the config.
* Health-check endpoint at ``/health``.


[1.0.3] - 2020-08-23
--------------------

Fixed
^^^^^

* More robust date parisng and correct handling of time zones.


[1.0.2] - 2020-06-08
--------------------

Fixed
^^^^^

* ADD CI and badges, no code changes.


[1.0.1] - 2020-06-08
--------------------

Fixed
^^^^^

* Fix missing package information.


[1.0.0] - 2020-06-28
--------------------

Initial public release.
