from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .infrai_sms import InfraiSmsClient, new_request_id


@dataclass(frozen=True)
class MediaAsset:
    asset_id: str
    title: str
    creator_phone: str


@dataclass(frozen=True)
class AssetJob:
    job_id: str
    asset: MediaAsset
    state: str


class CreatorAlertService:
    def __init__(self, sms: InfraiSmsClient):
        self.sms = sms

    def deliver(self, job: AssetJob) -> dict[str, Any] | None:
        if job.state != "ready":
            return None
        text = f"Media ready: {job.asset.title} ({job.job_id})"
        return self.sms.send(job.asset.creator_phone, text, new_request_id(job.job_id))
