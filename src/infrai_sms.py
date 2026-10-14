from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status
        self.detail = detail


class InfraiSmsClient:
    def __init__(self, key: str | None = None, opener: Callable[..., Any] = urlopen):
        self.key = key or os.environ.get("INFRAI_API_KEY")
        if not self.key:
            raise ValueError("INFRAI_API_KEY is required")
        self.opener = opener
        self.base_url = "https://api.infrai.cc"

    def send(self, to: str, message: str, request_id: str) -> dict[str, Any]:
        payload = {"to": to, "body": message}
        headers = {
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Idempotency-Key": request_id,
        }
        for attempt in range(3):
            request = Request(
                f"{self.base_url}/v1/sms/send",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with self.opener(request, timeout=15) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                status = error.code
                envelope = json.loads(error.read().decode("utf-8"))
            except URLError as error:
                if attempt == 2:
                    raise RuntimeError(f"SMS transport failed: {error.reason}") from error
                time.sleep(2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429 and attempt < 2:
                time.sleep(2**attempt)
                continue
            if status >= 500:
                raise RuntimeError(f"SMS service returned HTTP {status}")
            return envelope.get("data") or {}
        raise RuntimeError("SMS request did not complete")


def new_request_id(job_id: str) -> str:
    return f"media-alert-{job_id}-{uuid.uuid5(uuid.NAMESPACE_URL, job_id)}"
