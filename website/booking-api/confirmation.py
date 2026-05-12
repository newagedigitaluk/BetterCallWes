"""Customer-facing booking confirmation email + SMS.

Templates mirror the SM8 templates Wes uses elsewhere on his account
(merge-field syntax matches), but are rendered server-side here
because the Messaging API doesn't apply SM8's template engine to raw
sends. Edit these constants if Wes changes his preferred wording.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ConfirmationContext:
    """Everything we need to render the customer-facing confirmation."""
    customer_first: str
    customer_last: str
    customer_email: str
    customer_phone: str
    service_name: str
    slot_start: datetime
    slot_end: datetime
    job_address: str
    estimated_total: float | None
    job_uuid: str

    @property
    def booking_date(self) -> str:
        # "Tuesday 21 May"
        return self.slot_start.strftime("%A %-d %B")

    @property
    def booking_time(self) -> str:
        # "09:00 to 10:00"
        return f"{self.slot_start.strftime('%H:%M')} to {self.slot_end.strftime('%H:%M')}"

    @property
    def booking_date_long(self) -> str:
        # "Tuesday 21st May 2026"
        d = self.slot_start.day
        suffix = "th" if 10 <= d <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")
        return self.slot_start.strftime(f"%A %-d{suffix} %B %Y")


VENDOR = {
    "name": "Better Call Wes",
    "phone": "07700 155 655",
    "phone_intl": "+447700155655",
    "email": "wes@bettercallwes.co.uk",
    "website": "bettercallwes.co.uk",
    "tagline": "Your Trusted Southampton Plumber & Heating Engineer",
    "logo_url": "https://bettercallwes.co.uk/assets/logo.webp",
    "gas_safe_reg": "558654",
}


# Plain-text email body. Mirrors Wes's existing template structure but
# avoids SM8 merge-field syntax (we substitute server-side).
EMAIL_SUBJECT = "Your Better Call Wes booking is confirmed — {date} at {time}"

EMAIL_TEXT_TEMPLATE = """\
BETTER CALL WES
Your Trusted Southampton Plumber & Heating Engineer

------------------------------------------------------------

Dear {first_name},

Thank you for booking with Better Call Wes Plumbing & Heating.

This email confirms your upcoming {service} appointment.

  Date:    {booking_date_long}
  Time:    {booking_time}
  Address: {job_address}

Please make sure someone is available at the property during this time. If anything changes or you need to reschedule, just let me know at least 24 hours in advance.

------------------------------------------------------------

CONTACT DETAILS
Phone:   {vendor_phone}
Email:   {vendor_email}
Website: {vendor_website}

------------------------------------------------------------

I look forward to helping with your {service} and ensuring everything runs smoothly on the day.

Warm regards,
Wes
Gas Safe Registered Engineer (#558654)
Better Call Wes — Your Local Southampton Plumber & Heating Engineer
Reliable. Trustworthy. Local.
"""

EMAIL_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>{subject}</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; color: #1F2937; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 24px;">

<table width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td style="padding-bottom: 16px; border-bottom: 2px solid #0F2942;">
      <img src="{logo_url}" alt="Better Call Wes" style="height: 60px; width: auto; display: block;">
      <div style="color: #0F2942; font-weight: 800; font-size: 20px; margin-top: 8px;">BETTER CALL WES</div>
      <div style="color: #64748B; font-size: 14px;">Your Trusted Southampton Plumber &amp; Heating Engineer</div>
    </td>
  </tr>
</table>

<p>Dear {first_name},</p>

<p>Thank you for booking with Better Call Wes Plumbing &amp; Heating.</p>

<p>This email confirms your upcoming <strong>{service}</strong> appointment.</p>

<table cellpadding="6" cellspacing="0" border="0" style="margin: 16px 0; background: #F8FAFC; border-radius: 8px; padding: 16px;">
  <tr><td style="font-weight: 600; padding-right: 16px;">Date:</td><td>{booking_date_long}</td></tr>
  <tr><td style="font-weight: 600; padding-right: 16px;">Time:</td><td>{booking_time}</td></tr>
  <tr><td style="font-weight: 600; padding-right: 16px;">Address:</td><td>{job_address}</td></tr>
</table>

<p>Please make sure someone is available at the property during this time. If anything changes or you need to reschedule, just let me know at least 24 hours in advance.</p>

<hr style="border: none; border-top: 1px solid #E5E7EB; margin: 24px 0;">

<table cellpadding="3" cellspacing="0" border="0">
  <tr><td style="font-weight: 600; padding-right: 12px;">Phone:</td><td><a href="tel:{vendor_phone_intl}" style="color: #FF6B00;">{vendor_phone}</a></td></tr>
  <tr><td style="font-weight: 600; padding-right: 12px;">WhatsApp:</td><td><a href="https://wa.me/{vendor_phone_intl_clean}" style="color: #25D366;">Message Wes on WhatsApp</a></td></tr>
  <tr><td style="font-weight: 600; padding-right: 12px;">Email:</td><td><a href="mailto:{vendor_email}" style="color: #FF6B00;">{vendor_email}</a></td></tr>
  <tr><td style="font-weight: 600; padding-right: 12px;">Website:</td><td><a href="https://{vendor_website}" style="color: #FF6B00;">{vendor_website}</a></td></tr>
</table>

<hr style="border: none; border-top: 1px solid #E5E7EB; margin: 24px 0;">

<p>I look forward to helping with your {service} and ensuring everything runs smoothly on the day.</p>

<p>Warm regards,<br>
<strong>Wes</strong><br>
Gas Safe Registered Engineer (#558654)<br>
Better Call Wes — Your Local Southampton Plumber &amp; Heating Engineer<br>
<em>Reliable. Trustworthy. Local.</em></p>

</body>
</html>
"""

# SMS — kept under 160 chars where possible (single segment) but UK SMS
# can handle multi-segment so don't sweat overflows.
SMS_TEMPLATE = (
    "Hi {first_name}, it's Wes from Better Call Wes Plumbing & Heating. "
    "Your {service} is booked for {booking_date_long} between {booking_time} at {short_address}. "
    "Questions or need to reschedule? Call or text me on {vendor_phone}."
)


def render_email(ctx: ConfirmationContext) -> tuple[str, str, str]:
    """Returns (subject, text_body, html_body)."""
    subject = EMAIL_SUBJECT.format(
        date=ctx.slot_start.strftime("%-d %B"),
        time=ctx.booking_time,
    )
    common = {
        "first_name": ctx.customer_first or "there",
        "service": ctx.service_name,
        "booking_date_long": ctx.booking_date_long,
        "booking_time": ctx.booking_time,
        "job_address": ctx.job_address,
        "vendor_phone": VENDOR["phone"],
        "vendor_phone_intl": VENDOR["phone_intl"],
        "vendor_phone_intl_clean": VENDOR["phone_intl"].lstrip("+"),
        "vendor_email": VENDOR["email"],
        "vendor_website": VENDOR["website"],
        "logo_url": VENDOR["logo_url"],
        "subject": subject,
    }
    text = EMAIL_TEXT_TEMPLATE.format(**common)
    html = EMAIL_HTML_TEMPLATE.format(**common)
    return subject, text, html


def render_sms(ctx: ConfirmationContext) -> str:
    return SMS_TEMPLATE.format(
        first_name=ctx.customer_first or "there",
        service=ctx.service_name,
        booking_date_long=ctx.booking_date_long,
        booking_time=ctx.booking_time,
        short_address=_short_address(ctx.job_address),
        vendor_phone=VENDOR["phone"],
    )


def _short_address(full: str) -> str:
    """Strip ', Southampton, United Kingdom' tail for SMS brevity."""
    parts = [p.strip() for p in full.split(",")]
    # Drop trailing 'United Kingdom' / 'UK'
    while parts and parts[-1].lower() in {"united kingdom", "uk", "great britain"}:
        parts.pop()
    return ", ".join(parts)


def parse_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(maxsplit=1)
    return parts[0], (parts[1] if len(parts) > 1 else "")


def normalise_uk_mobile(raw: str) -> str:
    """Best-effort normaliser. SM8 SMS endpoint accepts E.164; we
    convert UK formats. Non-UK numbers passed through untouched."""
    cleaned = "".join(ch for ch in raw if ch.isdigit() or ch == "+")
    if cleaned.startswith("+"):
        return cleaned
    if cleaned.startswith("07") and len(cleaned) == 11:
        return "+44" + cleaned[1:]
    if cleaned.startswith("447"):
        return "+" + cleaned
    if cleaned.startswith("7") and len(cleaned) == 10:
        return "+44" + cleaned
    return raw  # unknown format, let SM8 reject if invalid
