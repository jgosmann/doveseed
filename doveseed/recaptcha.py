import json
import logging
from typing import Optional
import urllib.request
from urllib.parse import urlencode
import re
import socket

from fastapi import Request, status
from fastapi.responses import PlainTextResponse


Logger = logging.getLogger(__name__)


class ReCaptchaMiddleware:
    def __init__(self, paths, config_path):
        self.paths = re.compile(paths)
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
        self.valid_hostnames = config["hostnames"]
        self._secret = config["secret"]

    async def __call__(self, request: Request, call_next):
        if self.paths.match(request.url.path) and request.method == "POST":
            data = await request.json()
            # pylint: disable=unsupported-membership-test,unsubscriptable-object
            if data is None or "captcha" not in data:
                return PlainTextResponse(
                    status_code=status.HTTP_400_BAD_REQUEST, content="Missing captcha."
                )
            if not self.verify_captcha(
                data["captcha"],
                socket.gethostbyname(request.client.host) if request.client else None,
            ):
                return PlainTextResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid captcha."
                )
        return await call_next(request)

    def verify_captcha(self, captcha: str, remote_ip: Optional[str]):
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
