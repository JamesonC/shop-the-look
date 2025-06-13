import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.test_config import reload_config


def test_public_url_strips_base_bucket(monkeypatch, tmp_path):
    env = tmp_path / ".env.development"
    env.write_text(
        "PINECONE_API_KEY=1\nPINECONE_INDEX_NAME=i\nPINECONE_TOP_K=1\n"
    )
    settings = reload_config(monkeypatch, env)
    # Import module after environment is prepared
    aws_storage = importlib.reload(importlib.import_module("api.aws_storage"))
    monkeypatch.setattr(aws_storage, "settings", settings, raising=False)
    settings.s3_bucket_name = "sock-design-bucket-development"

    url = aws_storage.public_url("sock-designs-bucket/batch1", "img.png")
    assert (
        url
        == "https://sock-design-bucket-development.s3.amazonaws.com/batch1/img.png"
    )



