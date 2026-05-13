"""ServiceM8 API client.

Thin wrapper around ServiceM8's REST API. Auth via X-Api-Key header.
Async (httpx) because FastAPI runs async by default and the booking
flow makes several SM8 calls per request.

Rate limits: 180 req/min, 20,000/day. Cache aggressively at the caller.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SM8_BASE = "https://api.servicem8.com/api_1.0"


class ServiceM8Error(Exception):
    """Raised when ServiceM8 returns an error or the response shape is unexpected."""


@dataclass
class CreatedJob:
    uuid: str
    location: str  # SM8 returns a relative URL pointing at the new job


class ServiceM8Client:
    """Single-instance ServiceM8 API client.

    Usage:
        sm8 = ServiceM8Client(api_key=os.environ["SERVICEM8_API_KEY"])
        async with sm8:
            materials = await sm8.list_materials()
    """

    def __init__(self, api_key: str, timeout_s: float = 20.0) -> None:
        if not api_key:
            raise ValueError("ServiceM8 API key is required")
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=SM8_BASE,
            timeout=timeout_s,
            headers={
                "X-Api-Key": api_key,
                "Accept": "application/json",
            },
        )

    async def __aenter__(self) -> "ServiceM8Client":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self._client.aclose()

    async def close(self) -> None:
        await self._client.aclose()

    # ─────────── Health / auth ───────────

    async def check_auth(self) -> dict[str, Any]:
        """Probe a known-good endpoint to verify the key works.

        ServiceM8 doesn't expose a dedicated account-info endpoint on the
        X-Api-Key auth path, so we GET /staff.json (always small, always
        accessible) and infer health from the response shape.
        """
        resp = await self._client.get("/staff.json")
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            raise ServiceM8Error(f"Unexpected staff.json response: {type(data).__name__}")
        active_staff = [s for s in data if s.get("active") in ("1", 1, True)]
        return {
            "ok": True,
            "staff_count": len(data),
            "active_staff": len(active_staff),
            "first_active": active_staff[0].get("email", "") if active_staff else "",
        }

    # ─────────── Materials (catalogue) ───────────

    async def list_materials(self) -> list[dict[str, Any]]:
        """Fetch all materials in the catalogue. ~93k records in BCW's
        account, so cache the result at the caller for several minutes."""
        resp = await self._client.get("/material.json")
        resp.raise_for_status()
        return resp.json()

    # ─────────── Job templates ───────────

    async def list_job_templates(self) -> list[dict[str, Any]]:
        resp = await self._client.get("/jobtemplate.json")
        resp.raise_for_status()
        return resp.json()

    # ─────────── Categories ───────────

    async def list_categories(self) -> list[dict[str, Any]]:
        resp = await self._client.get("/category.json")
        resp.raise_for_status()
        return resp.json()

    # ─────────── Activity (calendar / diary) ───────────

    async def list_activity(
        self,
        staff_uuid: str,
        start_date: str,
    ) -> list[dict[str, Any]]:
        """Fetch all scheduled activities for a staff member from start_date onwards.

        OData filter syntax: `staff_uuid eq <uuid> and start_date gt 'YYYY-MM-DD'`
        Note: SM8's OData implementation uses simple `eq` / `gt` / `lt` / `and`
        and date strings should be quoted.
        """
        filter_q = (
            f"staff_uuid eq {staff_uuid} and start_date gt '{start_date}'"
        )
        resp = await self._client.get(
            "/jobactivity.json",
            params={"$filter": filter_q, "$orderby": "start_date"},
        )
        resp.raise_for_status()
        return resp.json()

    async def create_activity(
        self,
        job_uuid: str,
        staff_uuid: str,
        start_iso: str,  # 'YYYY-MM-DD HH:MM:SS'
        end_iso: str,
    ) -> str:
        """Write a scheduled block onto the diary. Returns new activity uuid."""
        body = {
            "job_uuid": job_uuid,
            "staff_uuid": staff_uuid,
            "start_date": start_iso,
            "end_date": end_iso,
            "activity_was_scheduled": "1",
            "active": "1",
        }
        resp = await self._client.post("/jobactivity.json", json=body)
        resp.raise_for_status()
        new_uuid = resp.headers.get("x-record-uuid", "")
        if not new_uuid:
            raise ServiceM8Error("create_activity: missing x-record-uuid header")
        return new_uuid

    async def list_activity_for_job(self, job_uuid: str) -> list[dict[str, Any]]:
        """All jobactivity records for a single job, active and inactive.

        Used for reschedule-count tracking — we soft-delete the old
        activity (set active=0) on each reschedule, so counting inactive
        scheduled records tells us how many reschedules the customer has
        used.
        """
        resp = await self._client.get(
            "/jobactivity.json",
            params={"$filter": f"job_uuid eq {job_uuid}"},
        )
        resp.raise_for_status()
        return resp.json()

    async def deactivate_activity(self, activity_uuid: str) -> None:
        """Soft-delete a jobactivity (sets active=0). Used on reschedule
        so we keep an audit trail rather than physically removing the
        old slot."""
        resp = await self._client.post(
            f"/jobactivity/{activity_uuid}.json",
            json={"active": "0"},
        )
        resp.raise_for_status()

    # ─────────── Job creation (the primitive) ───────────

    async def create_job_from_template(
        self,
        template_uuid: str,
        *,
        company_name: str | None = None,
        company_uuid: str | None = None,
        job_address: str,
        job_description: str,
        first_name: str | None = None,
        last_name: str | None = None,
        mobile: str | None = None,
        phone: str | None = None,
        email: str | None = None,
    ) -> CreatedJob:
        """POST /jobtemplate/{uuid}/job.json — the booking primitive.

        Either company_name (creates a new company) or company_uuid (uses
        existing) must be provided. The template's badges + materials are
        auto-cloned into the new job.

        Customer contact details (first_name, last_name, mobile, email,
        phone) are optional but STRONGLY recommended: when passed, SM8
        creates the company AND a primary company contact AND wires that
        contact to the job in one transaction. Skipping them leaves the
        job's "Job Contact" field empty in the SM8 UI even if the company
        record exists.
        """
        if not (company_name or company_uuid):
            raise ValueError("Either company_name or company_uuid required")
        body: dict[str, str] = {
            "job_address": job_address,
            "job_description": job_description,
        }
        if company_uuid:
            body["company_uuid"] = company_uuid
        else:
            body["company_name"] = company_name  # type: ignore[assignment]
        # Customer contact — passed to the template endpoint so SM8
        # creates + wires the primary job contact atomically.
        if first_name:
            body["first_name"] = first_name
        if last_name:
            body["last_name"] = last_name
        if mobile:
            body["mobile"] = mobile
        if phone:
            body["phone"] = phone
        if email:
            body["email"] = email
        resp = await self._client.post(
            f"/jobtemplate/{template_uuid}/job.json",
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        job_uuid = data.get("jobUUID") or data.get("uuid")
        if not job_uuid:
            raise ServiceM8Error(f"create_job: no jobUUID in response: {data}")
        return CreatedJob(uuid=job_uuid, location=data.get("location", ""))

    async def get_job(self, job_uuid: str) -> dict[str, Any]:
        """Fetch a single job record by UUID."""
        resp = await self._client.get(f"/job/{job_uuid}.json")
        resp.raise_for_status()
        return resp.json()

    async def update_job(self, job_uuid: str, fields: dict[str, Any]) -> None:
        """Update specific fields on a job (e.g. category_uuid)."""
        resp = await self._client.post(f"/job/{job_uuid}.json", json=fields)
        resp.raise_for_status()

    async def delete_job(self, job_uuid: str) -> None:
        """Soft-delete (sets active=0)."""
        resp = await self._client.delete(f"/job/{job_uuid}.json")
        resp.raise_for_status()

    async def mark_job_unsuccessful(
        self,
        job_uuid: str,
        *,
        reason: str = "",
    ) -> None:
        """Mark the job as "Unsuccessful" with an optional cancellation reason.

        Unlike delete_job (which sets active=0 and hides the job),
        Unsuccessful keeps the job visible in SM8's Unsuccessful tab —
        useful for spotting patterns in why customers cancel.

        The reason text lands in SM8's `unsuccessful_reason` field
        (visible in the "Reason for cancellation" UI section).
        """
        body: dict[str, Any] = {"status": "Unsuccessful"}
        if reason:
            body["unsuccessful_reason"] = reason
        resp = await self._client.post(f"/job/{job_uuid}.json", json=body)
        resp.raise_for_status()

    # ─────────── jobmaterial (line items) ───────────

    async def add_job_material(
        self,
        *,
        job_uuid: str,
        material_uuid: str,
        quantity: float,
        price: float,
        name: str,
        sort_order: int = 300,
    ) -> str:
        """Append a line item to a job. `displayed_amount` MUST equal `price`."""
        body = {
            "job_uuid": job_uuid,
            "material_uuid": material_uuid,
            "quantity": f"{quantity:.4f}",
            "price": f"{price:.4f}",
            "displayed_amount": f"{price:.4f}",
            "displayed_amount_is_tax_inclusive": "1",
            "name": name,
            "sort_order": str(sort_order),
        }
        resp = await self._client.post("/jobmaterial.json", json=body)
        resp.raise_for_status()
        new_uuid = resp.headers.get("x-record-uuid", "")
        if not new_uuid:
            raise ServiceM8Error("add_job_material: missing x-record-uuid header")
        return new_uuid

    # ─────────── Contacts ───────────

    async def add_company_contact(
        self,
        *,
        company_uuid: str,
        first: str,
        last: str = "",
        mobile: str = "",
        phone: str = "",
        email: str = "",
        type_: str = "JOB",
    ) -> str:
        """Attach a contact to a company. type_ JOB means job contact."""
        body = {
            "company_uuid": company_uuid,
            "first": first,
            "last": last,
            "mobile": mobile,
            "phone": phone,
            "email": email,
            "type": type_,
            "active": "1",
        }
        resp = await self._client.post("/companycontact.json", json=body)
        resp.raise_for_status()
        return resp.headers.get("x-record-uuid", "")

    # ─────────── Messaging API ───────────
    #
    # Despite the public docs claiming the Messaging API requires
    # OAuth 2.0, X-Api-Key auth works fine — verified against a live
    # endpoint and confirmed by ServiceM8's own n8n community node
    # which uses only the API key. The Messaging endpoints sit at
    # api.servicem8.com/platform_service_* (note: NOT under /api_1.0/).

    async def send_email(
        self,
        *,
        to: str,
        subject: str,
        text_body: str = "",
        html_body: str = "",
        reply_to: str | None = None,
        regarding_job_uuid: str | None = None,
        impersonate_uuid: str | None = None,
    ) -> dict[str, Any]:
        """POST /platform_service_email. Sends through SM8's email service.

        At least one of text_body or html_body must be provided.
        regarding_job_uuid links the email to a job (appears in its diary).
        impersonate_uuid is required if the body uses <platform-user-signature/>.
        """
        if not (text_body or html_body):
            raise ValueError("send_email: textBody or htmlBody required")
        body: dict[str, Any] = {"to": to, "subject": subject}
        if text_body:
            body["textBody"] = text_body
        if html_body:
            body["htmlBody"] = html_body
        if reply_to:
            body["replyTo"] = reply_to
        if regarding_job_uuid:
            body["regardingJobUUID"] = regarding_job_uuid
        headers = {
            "X-Api-Key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if impersonate_uuid:
            headers["x-impersonate-uuid"] = impersonate_uuid
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://api.servicem8.com/platform_service_email",
                json=body,
                headers=headers,
            )
        resp.raise_for_status()
        return resp.json()

    async def send_sms(
        self,
        *,
        to: str,
        message: str,
        regarding_job_uuid: str | None = None,
    ) -> dict[str, Any]:
        """POST /platform_service_sms. Sends through SM8's SMS service.

        SM8 charges per outbound SMS — typically a few pence per UK msg.
        regarding_job_uuid links the SMS to a job (appears in its diary).
        """
        body: dict[str, Any] = {"to": to, "message": message}
        if regarding_job_uuid:
            body["regardingJobUUID"] = regarding_job_uuid
        headers = {
            "X-Api-Key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://api.servicem8.com/platform_service_sms",
                json=body,
                headers=headers,
            )
        resp.raise_for_status()
        return resp.json()
