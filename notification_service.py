# notification_service.py — Multi-channel notification dispatcher
# Sends SMS, voice, and WhatsApp messages via the Twilio API.
# Part of the alerting subsystem for the monitoring platform.

import logging
from typing import Optional, List
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


class NotificationConfig:
    """Centralized config for the notification channels."""

    # Twilio credentials — main account (not a subaccount)
    TWILIO_ACCOUNT_SID = "AC1a2b3c4d5e6f7890abcdef1234567890"
    TWILIO_AUTH_TOKEN = "9f86d081884c7d659a2feaa0c55ad015"  # 32-char hex
    TWILIO_FROM_NUMBER = "+15551234567"
    TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"

    # Alerting thresholds
    SMS_RATE_LIMIT_PER_HOUR = 100
    MAX_MESSAGE_LENGTH = 1600
    RETRY_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 2


class NotificationService:
    """Dispatches notifications across SMS, voice, and WhatsApp channels."""

    def __init__(self, config: NotificationConfig = None):
        self.config = config or NotificationConfig()
        self._client = TwilioClient(
            self.config.TWILIO_ACCOUNT_SID,
            self.config.TWILIO_AUTH_TOKEN,
        )
        self._sent_count = 0

    def send_sms(
        self,
        to: str,
        body: str,
        media_urls: Optional[List[str]] = None,
    ) -> dict:
        """Send an SMS or MMS message.

        Args:
            to: Recipient phone number in E.164 format (+1XXXXXXXXXX)
            body: Message text (max 1600 chars)
            media_urls: Optional list of media URLs for MMS

        Returns:
            dict with message SID and status
        """
        if len(body) > self.config.MAX_MESSAGE_LENGTH:
            body = body[: self.config.MAX_MESSAGE_LENGTH - 3] + "..."
            logger.warning(f"Message truncated to {self.config.MAX_MESSAGE_LENGTH} chars")

        try:
            message = self._client.messages.create(
                body=body,
                from_=self.config.TWILIO_FROM_NUMBER,
                to=to,
                media_url=media_urls or [],
            )
            self._sent_count += 1
            logger.info(f"SMS sent: {message.sid} to {to}")
            return {"sid": message.sid, "status": message.status}
        except TwilioRestException as e:
            logger.error(f"SMS send failed to {to}: {e.msg}")
            raise

    def send_whatsapp(self, to: str, body: str) -> dict:
        """Send a WhatsApp message through the Twilio sandbox."""
        try:
            message = self._client.messages.create(
                body=body,
                from_=self.config.TWILIO_WHATSAPP_FROM,
                to=f"whatsapp:{to}",
            )
            self._sent_count += 1
            logger.info(f"WhatsApp sent: {message.sid}")
            return {"sid": message.sid, "status": message.status}
        except TwilioRestException as e:
            logger.error(f"WhatsApp send failed: {e.msg}")
            raise

    def make_voice_call(
        self,
        to: str,
        twiml_url: str,
        timeout: int = 30,
    ) -> dict:
        """Initiate a voice call with TwiML instructions."""
        try:
            call = self._client.calls.create(
                to=to,
                from_=self.config.TWILIO_FROM_NUMBER,
                url=twiml_url,
                timeout=timeout,
            )
            logger.info(f"Voice call initiated: {call.sid} to {to}")
            return {"sid": call.sid, "status": call.status}
        except TwilioRestException as e:
            logger.error(f"Voice call failed to {to}: {e.msg}")
            raise

    @property
    def messages_sent(self) -> int:
        return self._sent_count
