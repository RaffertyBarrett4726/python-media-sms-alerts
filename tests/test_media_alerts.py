import json

from src.infrai_sms import InfraiSmsClient
from src.media_alerts import AssetJob, CreatorAlertService, MediaAsset


class RecordingSms:
    def __init__(self):
        self.calls = []

    def send(self, to, message, request_id):
        self.calls.append((to, message, request_id))
        return {"message_id": "m-17"}


def test_ready_job_delivers_creator_alert():
    sms = RecordingSms()
    job = AssetJob("job-17", MediaAsset("asset-17", "Episode 17", "+15550100"), "ready")

    result = CreatorAlertService(sms).deliver(job)

    assert result == {"message_id": "m-17"}
    assert sms.calls[0][0] == "+15550100"
    assert "Episode 17" in sms.calls[0][1]
    assert "job-17" in sms.calls[0][1]


def test_processing_job_does_not_alert_creator():
    sms = RecordingSms()
    job = AssetJob("job-18", MediaAsset("asset-18", "Episode 18", "+15550101"), "processing")

    assert CreatorAlertService(sms).deliver(job) is None
    assert sms.calls == []


def test_sms_client_uses_contract_body_field():
    requests = []

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return b'{"ok": true, "data": {"message_id": "m-17"}}'

    def opener(request, timeout):
        requests.append(request)
        return Response()

    result = InfraiSmsClient(key="test-key", opener=opener).send("+15550100", "Ready", "job-17")

    assert result == {"message_id": "m-17"}
    assert json.loads(requests[0].data) == {"to": "+15550100", "body": "Ready"}
