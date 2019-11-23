import http
import json
import logging
import urllib.request
from urllib.parse import urlencode
import re

import werkzeug.wrappers


Logger = logging.getLogger(__name__)


class ReCaptchaMiddleware:
    def __init__(self, app, paths, valid_hostnames, secret):
        self.app = app
        self.paths = re.compile(paths)
        self.valid_hostnames = valid_hostnames
        self._secret = secret

    def __call__(self, environ, start_response):
        request = werkzeug.wrappers.Request(environ)
        if self.paths.match(request.path):
            if not self.verify_captcha(
                request.get_json()["captcha"], request.remote_addr
            ):
                return "Invalid captcha.", http.HTTPStatus.UNAUTHORIZED
        return self.app(environ, start_response)

    def verify_captcha(self, captcha: str, remote_ip: str):
        verification_request = urllib.request.Request(
            "https://www.google.com/recaptcha/api/siteverify",
            method="post",
            data=urlencode(
                {"secret": self._secret, "response": captcha, "remoteip": remote_ip}
            ).encode("ascii"),
        )
        with urllib.request.urlopen(verification_request) as f:
            result = json.loads(f.read())
        if len(result.get("error-codes", [])) > 0:
            Logger.warning(result["error-codes"])
        return result["success"] and result["hostname"] in self.valid_hostnames
