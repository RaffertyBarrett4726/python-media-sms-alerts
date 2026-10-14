from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.infrai_sms import InfraiSmsClient
from src.media_alerts import AssetJob, CreatorAlertService, MediaAsset


class DemoSms:
    def send(self, to: str, message: str, request_id: str) -> dict[str, str]:
        print(f"dry-run SMS to {to}: {message} [{request_id}]")
        return {"message_id": "demo-message"}


asset = MediaAsset("asset-17", "Episode 17", "+15550100")
job = AssetJob("job-17", asset, "ready")
sender = InfraiSmsClient() if os.environ.get("RUN_LIVE") == "1" else DemoSms()
print(CreatorAlertService(sender).deliver(job))
