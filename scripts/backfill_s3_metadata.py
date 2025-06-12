#!/usr/bin/env python
"""Backfill S3 metadata for existing Pinecone vectors."""

import logging
import os
from typing import List

from pinecone import Pinecone
from api.config import settings


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def get_index() -> "Index":
    """Initialize Pinecone index using environment variables."""
    api_key = os.getenv("PINECONE_API_KEY")
    environment = os.getenv("PINECONE_ENVIRONMENT")
    index_name = os.getenv("PINECONE_INDEX_NAME")

    missing = [v for v in ["PINECONE_API_KEY", "PINECONE_ENVIRONMENT", "PINECONE_INDEX_NAME"] if not os.getenv(v)]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    pc = Pinecone(api_key=api_key, environment=environment)
    return pc.Index(index_name)


def chunked(iterable: List[str], size: int) -> List[List[str]]:
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


def main() -> None:
    index = get_index()

    logging.info("Fetching vector ids from index…")
    vector_ids: List[str] = []
    try:
        for batch in index.list():
            vector_ids.extend(batch)
    except Exception as exc:
        logging.error("Failed to list vectors: %s", exc)
        return

    logging.info("%d vectors found", len(vector_ids))

    for id_batch in chunked(vector_ids, 100):
        try:
            fetched = index.fetch(ids=id_batch)
        except Exception as exc:
            logging.error("Failed to fetch batch %s: %s", id_batch, exc)
            continue

        upserts = []
        vectors = fetched.get("vectors", {})
        for vid, record in vectors.items():
            metadata = record.get("metadata") or {}
            gcs_name = metadata.get("gcs_file_name")
            gcs_path = metadata.get("gcs_file_path")
            if not gcs_name or not gcs_path:
                logging.warning("Vector %s missing gcs metadata; skipping", vid)
                continue

            new_meta = dict(metadata)
            new_meta["s3_file_name"] = gcs_name
            new_meta["s3_file_path"] = gcs_path.removeprefix(f"{settings.s3_bucket_name}/")

            upserts.append({
                "id": vid,
                "values": record.get("values"),
                "metadata": new_meta,
            })

        if not upserts:
            continue

        try:
            index.upsert(vectors=upserts)
            logging.info("Upserted %d vectors", len(upserts))
        except Exception as exc:
            logging.error("Failed to upsert batch starting with %s: %s", id_batch[0], exc)

    logging.info("Backfill complete")


if __name__ == "__main__":
    main()
