"""Pluggable cache for geoglows plot CSVs.

Two backends, chosen by the GEOGLOWS_CACHE_BACKEND env var:
  * "workspace" (default) -- the Tethys app workspace (local / EFS). Original behavior.
  * "s3"                   -- an S3 bucket + prefix. Durable and shared across tasks, which is
                             required for stateless deployments (e.g. Fargate with no EFS) where
                             the app workspace is ephemeral and per-container.

Cache objects are daily CSVs named "<plot_name>-<river_id>-<YYYYMMDD>.csv" -- one current file per
(plot_name, river_id). Callers handle the per-plot DataFrame parsing; a backend only stores/loads
the raw CSV and reports the latest cached date.

S3 backend config (when GEOGLOWS_CACHE_BACKEND=s3):
  GEOGLOWS_CACHE_BUCKET   required -- bucket name
  GEOGLOWS_CACHE_PREFIX   optional -- key prefix (default "cache/geoglows")
  AWS_REGION              optional -- region (default "us-east-1")
boto3 must be installed for the s3 backend: pip install "tethysdash-plugin-geoglows[s3]".
"""

import io
import os


def _name(plot_name, river_id, date):
    return f"{plot_name}-{river_id}-{date}.csv"


def _prefix(plot_name, river_id):
    return f"{plot_name}-{river_id}-"


def _date_from_name(name):
    # "forecast-12345-20260625.csv" (or an S3 key ending in it) -> "20260625"
    return name.rsplit("-", 1)[-1].split(".")[0]


class WorkspaceCache:
    """Cache under the Tethys app workspace (local / EFS). Original plugin behavior."""

    def __init__(self):
        from tethysapp.tethysdash.app import App

        workspace_path = App.get_app_workspace()
        self.root = os.path.join(workspace_path.path, "geoglows_plots_cache")
        if not os.path.exists(self.root):
            os.makedirs(self.root, exist_ok=True)
            self._chown(self.root)

    @staticmethod
    def _chown(path):
        # Best-effort: preserve the legacy chown-to-serving-user behavior, but never fail on a
        # non-root / no-such-user environment.
        try:
            import getpass
            import pwd

            username = os.environ.get("NGINX_USER", getpass.getuser())
            pw = pwd.getpwnam(username)
            os.chown(path, pw.pw_uid, pw.pw_gid)
        except Exception:
            pass

    def latest_date(self, plot_name, river_id):
        pre = _prefix(plot_name, river_id)
        dates = [_date_from_name(f) for f in os.listdir(self.root) if f.startswith(pre)]
        return max(dates) if dates else None

    def open(self, plot_name, river_id, date):
        # Returns a path; pandas.read_csv accepts it directly.
        return os.path.join(self.root, _name(plot_name, river_id, date))

    def write(self, plot_name, river_id, date, df):
        pre = _prefix(plot_name, river_id)
        for f in os.listdir(self.root):  # drop stale dates for this plot/river
            if f.startswith(pre):
                try:
                    os.remove(os.path.join(self.root, f))
                except OSError:
                    pass
        df.to_csv(os.path.join(self.root, _name(plot_name, river_id, date)))


class S3Cache:
    """Durable, shared cache in an S3 bucket/prefix (for stateless deployments)."""

    def __init__(self):
        import boto3

        self.bucket = os.environ["GEOGLOWS_CACHE_BUCKET"]
        self.prefix = os.environ.get("GEOGLOWS_CACHE_PREFIX", "cache/geoglows").strip("/")
        self.client = boto3.client(
            "s3", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )

    def _key(self, plot_name, river_id, date):
        return f"{self.prefix}/{_name(plot_name, river_id, date)}"

    def _key_prefix(self, plot_name, river_id):
        return f"{self.prefix}/{_prefix(plot_name, river_id)}"

    def latest_date(self, plot_name, river_id):
        resp = self.client.list_objects_v2(
            Bucket=self.bucket, Prefix=self._key_prefix(plot_name, river_id)
        )
        dates = [_date_from_name(o["Key"]) for o in resp.get("Contents", [])]
        return max(dates) if dates else None

    def open(self, plot_name, river_id, date):
        obj = self.client.get_object(
            Bucket=self.bucket, Key=self._key(plot_name, river_id, date)
        )
        return io.BytesIO(obj["Body"].read())  # pandas.read_csv accepts a file-like

    def write(self, plot_name, river_id, date, df):
        buf = io.StringIO()
        df.to_csv(buf)
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._key(plot_name, river_id, date),
            Body=buf.getvalue().encode(),
        )
        # Drop stale dates for this plot/river (an S3 lifecycle rule can also expire the prefix).
        keep = self._key(plot_name, river_id, date)
        resp = self.client.list_objects_v2(
            Bucket=self.bucket, Prefix=self._key_prefix(plot_name, river_id)
        )
        stale = [{"Key": o["Key"]} for o in resp.get("Contents", []) if o["Key"] != keep]
        if stale:
            self.client.delete_objects(Bucket=self.bucket, Delete={"Objects": stale})


def get_cache():
    """Return the cache backend selected by GEOGLOWS_CACHE_BACKEND (default 'workspace')."""
    backend = os.environ.get("GEOGLOWS_CACHE_BACKEND", "workspace").strip().lower()
    if backend == "s3":
        return S3Cache()
    return WorkspaceCache()
