from base64 import b64encode
from datetime import datetime
from typing import Dict
from urllib.parse import quote

from jinja2 import BaseLoader
import pytest

from doveseed.email_templating import EmailFromTemplateProvider
from doveseed.domain_types import Action, Email, FeedItem, Token


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
        confirm_url_format="https://{host}/confirm/{email}?token={token}",
    )


@pytest.fixture
def feed_item():
    return FeedItem(
        title="title",
        link="link",
        pub_date=datetime(2019, 11, 22),
        description="description",
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
            binary_loader=MockBinaryLoader(dict()),
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
            binary_loader=MockBinaryLoader(dict()),
        )
        msg = provider.get_confirmation_request_msg(
            Email("email@local"), action=Action.subscribe, confirm_token=token
        )

        expected_link = "https://test.local/confirm/email%40local?token=" + quote(
            token.to_string()
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
            binary_loader=MockBinaryLoader(dict()),
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
            binary_loader=MockBinaryLoader(dict()),
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
                    f"subscribe.subject.txt": subject,
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
        to_email = Email("to.email@test.org")
        subject = "subject"
        plain_text = "plain text"
        html = "html"

        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    f"new-post.subject.txt": subject,
                    f"new-post.txt": plain_text,
                    f"new-post.html": html,
                }
            ),
            binary_loader=MockBinaryLoader(dict()),
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
            binary_loader=MockBinaryLoader(dict()),
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
            binary_loader=MockBinaryLoader(dict()),
        )
        msg = provider.get_new_post_msg(feed_item, Email("email"))

        assert (
            msg.get_body("plain").get_content().strip()  # type: ignore
            == f"{subject} {settings.display_name} {settings.host} email title"
        )

    def test_include_binary_and_b64encode(self, feed_item, settings):
        binary_content = b"binary content"
        subject = "{{ include_binary('bin') | b64encode }}"
        provider = EmailFromTemplateProvider(
            settings=settings,
            template_loader=MockTemplateLoader(
                {
                    f"new-post.subject.txt": subject,
                    "new-post.txt": "",
                    "new-post.html": "",
                }
            ),
            binary_loader=MockBinaryLoader({"bin": binary_content}),
        )
        msg = provider.get_new_post_msg(feed_item, Email("email"))

        assert msg["Subject"] == b64encode(binary_content).decode("ascii")
