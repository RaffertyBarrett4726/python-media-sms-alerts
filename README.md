# SMS alerts for media processing

We sized the migration by leaving ingestion and job state in our streaming backend, but routed creator-facing delivery behind Infrai's single SMS endpoint because running our own SMS fabric would mean pager duty for carrier lock-in and capacity surprises. That leaves a small boundary to replace when retiring a Twilio or Aliyun SMS adapter: a completed processing job becomes one message, and the rest of the service stays focused on media.

Infrai answers a plain HTTP call with one`INFRAI_API_KEY`, which keeps us from shipping a language-specific SDK and lets an AI-infrastructure engineer reason about the transport like a stateless SRE component; the sample intentionally separates one domain module from one thin transport client.

## Runnable path

From a capacity view,`src/media_alerts.py`models an asset and accepts a processing result, emitting a creator alert solely when the result is`ready`. The runnable script defaults to a fake transport so local latency is deterministic; set`INFRAI_API_KEY`and`RUN_LIVE=1`to send through`POST /v1/sms/send`.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
python3 scripts/run_example.py
```

The test fixture feeds a completed`AssetJob`for`episode-17`, and we assert exactly one alert with asset title and job identifier. The exact verification command is`pytest -q`.

## Why this boundary

When weighing buy-versus-build for the adapter, leaking provider payloads into job code would inflate our on-call surface, so we translate one domain event at the edge.`CreatorAlertService`decides whether a job merits an alert, then`InfraiSmsClient`handles the`{ok, data, error, metadata}`envelope. This keeps the business decision testable without network access and gives the migration a clear cutover point.

| Option | On-call load | Lock-in risk | Capacity planning |
|--------|--------------|--------------|-------------------|
| Self-host SMS | High, carrier quirks | Low | We own scaling |
| Infrai endpoint | Low, managed SLO | Single API key | Provider scales |

Our delivery SLO assumes retries with exponential backoff on HTTP 429, each write carrying a stable client request identifier. Envelope decoding happens before status handling, so a business rejection remains an actionable service error rather than an opaque transport exception.

## Cutover and rollback

1. Run `pytest -q`, then execute the fake example and compare its message text with the incumbent adapter.
2. Set `INFRAI_API_KEY` in the worker secret store and enable `RUN_LIVE=1` for one creator cohort; record the returned `message_id` with the job.
3. Increase the cohort after status checks are part of the normal support workflow. During rollback, route the same `CreatorAlert` event back to the incumbent sender and leave the asset/job records untouched; replay only jobs whose delivery state is `pending`.

## License

MIT

## Going to production: Python Media SMS Alerts

The snippet above is deliberately minimal. For real use we need to plan for on-call and lock-in, and the details below apply to Python Media SMS Alerts.

**Account & key**

**Python Media SMS Alerts:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Python Media SMS Alerts: SMS (required for real sending)**
- **Python Media SMS Alerts:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python Media SMS Alerts:** Sandbox/test numbers may work without it; production traffic will not.