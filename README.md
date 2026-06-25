
## Plot data caching

The geoglows plot helpers cache each day's API responses as CSVs (one per plot type + river id).
The cache backend is selected with the `GEOGLOWS_CACHE_BACKEND` environment variable:

- `workspace` (default) — the Tethys app workspace (local disk / EFS). Original behavior.
- `s3` — an S3 bucket + prefix. Durable and shared across tasks; use this for stateless deployments
  (e.g. Fargate without EFS) where the app workspace is ephemeral.

S3 backend env vars:

| Variable | Required | Default | Notes |
|---|---|---|---|
| `GEOGLOWS_CACHE_BUCKET` | yes | — | S3 bucket name |
| `GEOGLOWS_CACHE_PREFIX` | no | `cache/geoglows` | key prefix |
| `AWS_REGION` | no | `us-east-1` | bucket region |

The s3 backend needs boto3: `pip install "tethysdash-plugin-geoglows[s3]"`. Credentials come from the
standard AWS chain (e.g. an ECS task role with `s3:GetObject`/`PutObject`/`ListBucket` on the prefix).
