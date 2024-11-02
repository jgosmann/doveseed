from base64 import b64decode, b64encode
from datetime import datetime
from typing import Dict
from urllib.parse import quote

import pytest
from jinja2 import BaseLoader

from doveseed.domain_types import Action, Email, FeedItem, Token
from doveseed.email_templating import (
    EmailFromTemplateProvider,
    RelatedPartInfo,
    _RelatedPartsCollector,
)


class MockTemplateLoader(BaseLoader):
    def __init__(self, template_sources: Dict[str, str]):
        self.template_sources = template_sources

    def get_source(self, environment, template):
        return self.template_sources[template], template, lambda: False


class MockBinaryLoader:
    def __init__(self, sources: Dict[str, bytes]):
        self.sources = sources

    def load(self, filename: str):
        return self.sources[filename]


@pytest.fixture
def settings():
    return EmailFromTemplateProvider.Settings(
        display_name="display_name",
        sender="sender <sender@test.org>",
        host="test.local",
        confirm_url_format="https://{host}/{action}/confirm/{email}?token={token}",
    )


@pytest.fixture
def feed_item():
    return FeedItem(
        title="title",
        link="link",
        pub_date=datetime(2019, 11, 22),
        description="description",
        image=None,
    )


class TestGetConfirmationRequestMsg:
    @pytest.mark.parametrize("action", (Action.subscribe, Action.unsubscribe))
    def test_constructs_email_message_from_templates(self, action, settings):
        to_email = Email("to.email@test.org")
        subject = "subject"
        plain_text = "plain text"
        html = "html"

        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    f"{action.name}.subject.txt": subject,
                    f"{action.name}.txt": plain_text,
                    f"{action.name}.html": html,
                }
            ),
            binary_loader=MockBinaryLoader({}),
        )
        msg = provider.get_confirmation_request_msg(
            to_email, action=action, confirm_token=Token(b"token")
        )

        assert msg["Subject"] == subject
        assert msg["To"] == to_email
        assert msg.get_body("plain").get_content().strip() == plain_text  # type: ignore
        assert msg.get_body("html").get_content().strip() == html  # type: ignore

    def test_confirm_link_substitutions(self, settings):
        template = "{{confirm_link}}"
        token = Token(b"token")

        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    "subscribe.subject.txt": template,
                    "subscribe.txt": template,
                    "subscribe.html": template,
                }
            ),
            binary_loader=MockBinaryLoader({}),
        )
        msg = provider.get_confirmation_request_msg(
            Email("email@local"), action=Action.subscribe, confirm_token=token
        )

        expected_link = (
            "https://test.local/subscribe/confirm/email%40local?token="
            + quote(token.to_string())
        )
        assert msg["Subject"] == expected_link
        assert (
            msg.get_body("plain").get_content().strip() == expected_link  # type: ignore
        )
        assert (
            msg.get_body("html").get_content().strip() == expected_link  # type: ignore
        )

    def test_subject_substitutions(self, settings):
        subject = "{{display_name}} {{host}} {{to_email}}"

        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    "subscribe.subject.txt": subject,
                    "subscribe.txt": "",
                    "subscribe.html": "",
                }
            ),
            binary_loader=MockBinaryLoader({}),
        )
        msg = provider.get_confirmation_request_msg(
            Email("email"), action=Action.subscribe, confirm_token=Token(b"token")
        )

        assert msg["Subject"] == f"{settings.display_name} {settings.host} email"

    def test_body_substitutions(self, settings):
        subject = "subject"
        template = "{{subject}} {{display_name}} {{host}} {{to_email}}"

        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    "subscribe.subject.txt": subject,
                    "subscribe.txt": template,
                    "subscribe.html": template,
                }
            ),
            binary_loader=MockBinaryLoader({}),
        )
        msg = provider.get_confirmation_request_msg(
            Email("email"), action=Action.subscribe, confirm_token=Token(b"token")
        )

        assert (
            msg.get_body("plain").get_content().strip()  # type: ignore
            == f"{subject} {settings.display_name} {settings.host} email"
        )

    def test_include_binary_and_b64encode(self, settings):
        binary_content = b"binary content"
        subject = "{{ include_binary('bin') | b64encode }}"
        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    "subscribe.subject.txt": subject,
                    "subscribe.txt": "",
                    "subscribe.html": "",
                }
            ),
            binary_loader=MockBinaryLoader({"bin": binary_content}),
        )
        msg = provider.get_confirmation_request_msg(
            Email("email"), action=Action.subscribe, confirm_token=Token(b"token")
        )

        assert msg["Subject"] == b64encode(binary_content).decode("ascii")


class TestGetNewPostMsg:
    def test_constructs_email_message_from_templates(self, feed_item, settings):
        subject = "subject"
        plain_text = "plain text"
        html = "html"

        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    "new-post.subject.txt": subject,
                    "new-post.txt": plain_text,
                    "new-post.html": html,
                }
            ),
            binary_loader=MockBinaryLoader({}),
        )
        msg = provider.get_new_post_msg(feed_item, Email("email"))

        assert msg["Subject"] == subject
        assert msg.get_body("plain").get_content().strip() == plain_text  # type: ignore
        assert msg.get_body("html").get_content().strip() == html  # type: ignore

    def test_subject_substitutions(self, feed_item, settings):
        subject = "{{display_name}} {{host}} {{to_email}} {{post.title}}"

        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    "new-post.subject.txt": subject,
                    "new-post.txt": "",
                    "new-post.html": "",
                }
            ),
            binary_loader=MockBinaryLoader({}),
        )
        msg = provider.get_new_post_msg(feed_item, Email("email"))

        assert msg["Subject"] == f"{settings.display_name} {settings.host} email title"

    def test_body_substitutions(self, feed_item, settings):
        subject = "subject"
        template = "{{subject}} {{display_name}} {{host}} {{to_email}} {{post.title}}"

        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    "new-post.subject.txt": subject,
                    "new-post.txt": template,
                    "new-post.html": template,
                }
            ),
            binary_loader=MockBinaryLoader({}),
        )
        msg = provider.get_new_post_msg(feed_item, Email("email"))

        assert (
            msg.get_body("plain").get_content().strip()  # type: ignore
            == f"{subject} {settings.display_name} {settings.host} email title"
        )

    def test_urlquote(self, feed_item, settings):
        subject = "{{ '@' | urlquote }}"
        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    "new-post.subject.txt": subject,
                    "new-post.txt": "",
                    "new-post.html": "",
                }
            ),
            binary_loader=MockBinaryLoader({}),
        )
        msg = provider.get_new_post_msg(feed_item, Email("email"))

        assert msg["Subject"] == "%40"

    def test_include_binary_and_b64encode(self, feed_item, settings):
        binary_content = b"binary content"
        subject = "{{ include_binary('bin') | b64encode }}"
        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    "new-post.subject.txt": subject,
                    "new-post.txt": "",
                    "new-post.html": "",
                }
            ),
            binary_loader=MockBinaryLoader({"bin": binary_content}),
        )
        msg = provider.get_new_post_msg(feed_item, Email("email"))

        assert msg["Subject"] == b64encode(binary_content).decode("ascii")

    def test_include_related_plain_text(self, feed_item, settings):
        binary_content = b"binary content"
        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    "new-post.subject.txt": "Include attachment",
                    "new-post.txt": "{{ include_related('bin').content_id }}",
                    "new-post.html": "",
                }
            ),
            binary_loader=MockBinaryLoader({"bin": binary_content}),
        )
        msg = provider.get_new_post_msg(feed_item, Email("email"))

        body = msg.get_body(("plain",))
        assert body
        payload = body.get_payload()
        assert payload
        content_id = str(payload).strip()

        assert [
            b64decode(str(part.get_payload() or ""))
            for part in msg.walk()
            if part.get("Content-ID", None) == content_id
        ] == [binary_content]

    def test_include_related_html(self, feed_item, settings):
        binary_content = b"binary content"
        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    "new-post.subject.txt": "Include attachment",
                    "new-post.txt": "",
                    "new-post.html": "{{ include_related('bin').content_id }}",
                }
            ),
            binary_loader=MockBinaryLoader({"bin": binary_content}),
        )
        msg = provider.get_new_post_msg(feed_item, Email("email"))

        body = msg.get_body(("html",))
        assert body
        payload = body.get_payload()
        assert payload
        content_id = str(payload).strip()

        assert [
            b64decode(str(part.get_payload() or ""))
            for part in msg.walk()
            if part.get("Content-ID", None) == content_id
        ] == [binary_content]


@pytest.mark.parametrize(
    "args,kwargs,expected",
    [
        (
            ("foo/bar/somefile.bin",),
            {},
            RelatedPartInfo(
                content_id="some-id",
                filename="somefile.bin",
                content_type=("application", "octet-stream"),
                path="foo/bar/somefile.bin",
            ),
        ),
        (
            ("image.jpg",),
            {},
            RelatedPartInfo(
                content_id="some-id",
                filename="image.jpg",
                content_type=("image", "jpeg"),
                path="image.jpg",
            ),
        ),
        (
            ("image.png",),
            {},
            RelatedPartInfo(
                content_id="some-id",
                filename="image.png",
                content_type=("image", "png"),
                path="image.png",
            ),
        ),
        (
            ("image.jpg",),
            {"filename": "foo.xyz", "content_type": ("application", "foo")},
            RelatedPartInfo(
                content_id="some-id",
                filename="foo.xyz",
                content_type=("application", "foo"),
                path="image.jpg",
            ),
        ),
    ],
)
def test_include_related(args, kwargs, expected):
    info = _RelatedPartsCollector("prefix", MockBinaryLoader({})).include_related(
        *args, **kwargs
    )
    assert info.filename == expected.filename
    assert info.content_type == expected.content_type
    assert info.path == expected.path
