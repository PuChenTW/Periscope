"""Email sending service with provider abstraction.

This module provides a pluggable email sender interface with a mock
implementation for testing and a base class for real SMTP/API providers.
"""

from abc import ABC, abstractmethod

from loguru import logger


class EmailSender(ABC):
    """Abstract base class for email providers."""

    @abstractmethod
    async def send(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body

        Returns:
            True if sent successfully, False otherwise
        """
        pass


class MockEmailSender(EmailSender):
    """Mock email sender that logs instead of actually sending.

    Used for testing and development when no real SMTP/API is configured.
    """

    async def send(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """
        Mock send: log the email instead of sending.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body

        Returns:
            Always True (simulates successful send)
        """
        logger.info(f"[MOCK EMAIL] To: {to_email}")
        logger.info(f"[MOCK EMAIL] Subject: {subject}")
        logger.info(f"[MOCK EMAIL] HTML Body Length: {len(html_body)} bytes")
        logger.info(f"[MOCK EMAIL] Text Body Length: {len(text_body)} bytes")

        return True


def create_email_sender() -> EmailSender:
    """
    Factory function to create email sender based on configuration.

    For MVP, always returns MockEmailSender.
    In the future, can be extended to support SMTP/SendGrid/SES based on config.

    Returns:
        EmailSender instance
    """
    # For now, always use mock sender
    # Future: Read from config and instantiate real provider
    return MockEmailSender()
