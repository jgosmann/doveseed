import http
import json
import logging
import urllib.request
from urllib.parse import urlencode
import re

import werkzeug.wrappers
import werkzeug.wrappers.json


Logger = logging.getLogger(__name__)


class JsonRequest(werkzeug.wrappers.json.JSONMixin, werkzeug.wrappers.Request):
    pass


class ReCaptchaMiddleware:
    def __init__(self, app, paths, config_path):
        self.app = app
        self.paths = re.compile(paths)
        with open(config_path) as f:
            config = json.load(f)
        self.valid_hostnames = config["hostnames"]
        self._secret = config["secret"]

    def __call__(self, environ, start_response):
        Logger.error("start")
        request = JsonRequest(environ)
        if self.paths.match(request.path) and request.method == "POST":
            data = request.get_json()
            if data is None or "captcha" not in data:
                return self._to_response(
                    environ,
                    start_response,
                    ("Missing captcha.", http.HTTPStatus.BAD_REQUEST),
                )
            if not self.verify_captcha(data["captcha"], request.remote_addr):
                return self._to_response(
                    environ,
                    start_response,
                    ("Invalid captcha.", http.HTTPStatus.UNAUTHORIZED),
                )
        return self.app(environ, start_response)

    def verify_captcha(self, captcha: str, remote_ip: str):
        verification_request = urllib.request.Request(
            "https://www.google.com/recaptcha/api/siteverify",
            method="POST",
            data=urlencode(
                {"secret": self._secret, "response": captcha, "remoteip": remote_ip}
            ).encode("ascii"),
        )
        with urllib.request.urlopen(verification_request) as f:
            result = json.loads(f.read())
        if len(result.get("error-codes", [])) > 0:
            Logger.warning(result["error-codes"])
        return result["success"] and result["hostname"] in self.valid_hostnames

    def _to_response(self, environ, start_response, response):
        return werkzeug.wrappers.Response(*response)(environ, start_response)
