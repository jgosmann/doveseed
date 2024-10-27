import json
import logging
import re
import socket
from typing import Optional

import aiohttp
from fastapi import Request, status
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

Logger = logging.getLogger(__name__)


class ReCaptchaMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, paths, config_path):
        super().__init__(app)
        self.paths = re.compile(paths)
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
        self.valid_hostnames = config["hostnames"]
        self._secret = config["secret"]

    async def dispatch(self, request: Request, call_next):
        if self.paths.match(request.url.path) and request.method == "POST":
            data = await request.json()
            # pylint: disable=unsupported-membership-test,unsubscriptable-object
            if data is None or "captcha" not in data:
                return PlainTextResponse(
                    status_code=status.HTTP_400_BAD_REQUEST, content="Missing captcha."
                )
            if not await self.verify_captcha(
                data["captcha"],
                socket.gethostbyname(request.client.host) if request.client else None,
            ):
                return PlainTextResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid captcha."
                )
        return await call_next(request)

    async def verify_captcha(self, captcha: str, remote_ip: Optional[str]):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": self._secret,
                    "response": captcha,
                    "remoteip": remote_ip,
                },
            ) as response:
                result = await response.json()
        if len(result.get("error-codes", [])) > 0:
            Logger.warning(result["error-codes"])
        return result["success"] and result["hostname"] in self.valid_hostnames
