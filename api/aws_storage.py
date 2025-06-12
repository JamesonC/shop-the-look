"""Utilities for interacting with AWS storage."""

from api.config import settings


def _split_bucket_prefix(path: str) -> tuple[str, str]:
    """Return bucket and key prefix from a path.

    If the path already contains the configured bucket name as the first
    component, that portion is removed from the prefix.
    """

    bucket = settings.s3_bucket_name or ""
    path = (path or "").lstrip("/")

    if bucket and path.startswith(bucket + "/"):
        prefix = path[len(bucket) + 1 :]
    elif not bucket and "/" in path:
        bucket, prefix = path.split("/", 1)
    else:
        prefix = path

    return bucket, prefix


def public_url(path: str | None, file_name: str | None) -> str:
    """Return public URL for an S3 object.

    The ``path`` may include the bucket name. If the bucket is missing, the
    configured ``S3_BUCKET_NAME`` is used. If no bucket is available, an empty
    string is returned.
    """

    bucket, prefix = _split_bucket_prefix(path or "")
    file_name = file_name or ""

    if not bucket:
        return ""

    if prefix and not prefix.endswith("/"):
        prefix += "/"

    key = f"{prefix}{file_name}" if file_name else prefix
    return f"https://{bucket}.s3.amazonaws.com/{key}"
