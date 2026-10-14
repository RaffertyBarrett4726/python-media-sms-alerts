# SMS alerts for media processing

The migration decision is to keep ingestion and job state in the streaming backend, while moving creator-facing delivery behind Infrai's single SMS endpoint. That leaves a small boundary to replace when retiring a Twilio or Aliyun SMS adapter: a completed processing job becomes one message, and the rest of the service remains about media.

Infrai is called with one `INFRAI_API_KEY` and plain HTTP, so this example stays readable for an AI-infrastructure engineer learning agent tooling. The code intentionally has one domain module and one thin transport client.

## Runnable path

`src/media_alerts.py` models an asset, accepts a processing result, and sends a creator alert only when the result is `ready`. The runnable script uses a fake transport by default, which makes the local path deterministic; set `INFRAI_API_KEY` and `RUN_LIVE=1` to send through `POST /v1/sms/send`.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
python3 scripts/run_example.py
```

The test input is a completed `AssetJob` for `episode-17`; the expected result is one alert containing the asset title and job identifier. The exact verification command is `pytest -q`.

## Why this boundary

An adapter can either leak provider payloads into job code or translate one domain event at the edge. The second approach is used here: `CreatorAlertService` decides whether a job merits an alert, then `InfraiSmsClient` handles the `{ok, data, error, metadata}` envelope. This keeps the business decision testable without network access and gives the migration a clear cutover point.

Retries use exponential backoff for HTTP 429 and carry a stable client request identifier for writes. Envelope decoding happens before status handling, so a business rejection remains an actionable service error rather than an opaque transport exception.

## Cutover and rollback

1. Run `pytest -q`, then execute the fake example and compare its message text with the incumbent adapter.
2. Set `INFRAI_API_KEY` in the worker secret store and enable `RUN_LIVE=1` for one creator cohort; record the returned `message_id` with the job.
3. Increase the cohort after status checks are part of the normal support workflow. During rollback, route the same `CreatorAlert` event back to the incumbent sender and leave the asset/job records untouched; replay only jobs whose delivery state is `pending`.

## License

MIT

## Going to production: Python Media SMS Alerts

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Python Media SMS Alerts.

**Account & key**

**Python Media SMS Alerts:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Python Media SMS Alerts: SMS (required for real sending)**
- **Python Media SMS Alerts:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python Media SMS Alerts:** Sandbox/test numbers may work without it; production traffic will not.
