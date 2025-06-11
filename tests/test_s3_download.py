try:
    import boto3
except Exception:  # pragma: no cover - boto3 may not be installed
    boto3 = None
import os
import pytest

def test_s3_smoke_download():
    if boto3 is None:
        pytest.skip("boto3 not installed")
    bucket = os.getenv("S3_SMOKE_BUCKET")
    key = os.getenv("S3_SMOKE_KEY")
    if not bucket or not key:
        pytest.skip("S3_SMOKE_BUCKET or S3_SMOKE_KEY not set")
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    resp = s3.get_object(Bucket=bucket, Key=key)
    data = resp["Body"].read()
    assert len(data) > 0
