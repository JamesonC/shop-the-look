"""
Image Embedding Generator and Upserter

This script processes images from an AWS S3 bucket,
generates embeddings using Vertex AI, and upserts them to a Pinecone index.

Requirements:
- Python 3.7+
- Google Cloud SDK
- Pinecone account
- Vertex AI API enabled in your Google Cloud project

Required Python packages:
- vertexai
- boto3
- pinecone-client
 - python-dotenv        # to load .env.<ENVIRONMENT> (or DOTENV_PATH) into os.environ

Usage:
1. Set up environment variables in `.env.<ENVIRONMENT>` (defaults to `.env.development`) or set ``DOTENV_PATH``.
2. Run the script with the required arguments:
   python image_embedding_processor.py -p your-gc-project-id -b your-s3-bucket-name -f your-s3-folder-name -i your-pinecone-index-name
"""

import os
import json
import base64
import time
import uuid
import tempfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv  # Load environment variables from .env files
import vertexai                                     # Vertex AI SDK for Python :contentReference[oaicite:2]{index=2}
from vertexai.vision_models import MultiModalEmbeddingModel, Image  # Multimodal embedding model :contentReference[oaicite:3]{index=3}

from google.oauth2 import service_account            # To create Credentials from base64 :contentReference[oaicite:4]{index=4}
import boto3                                         # AWS S3 client

from pinecone import Pinecone                         # New Pinecone constructor (v3.x+) :contentReference[oaicite:6]{index=6}

# Constants
# Load environment variables using the same logic as ``api.config``. ``DOTENV_PATH``
# overrides the automatically derived ``../.env.<ENVIRONMENT>`` file.
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
dotenv_path = os.getenv("DOTENV_PATH") or os.path.join(
    os.path.dirname(__file__), f"../.env.{ENVIRONMENT}"
)
load_dotenv(dotenv_path=dotenv_path, override=True)

REGION = os.getenv("GOOGLE_CLOUD_PROJECT_LOCATION", "us-east1")  # e.g., "us-east1" :contentReference[oaicite:8]{index=8}
FILE_TYPE = 'image'


def initialize_vertex_ai():
    """Decode base64 JSON, build service-account creds, and init Vertex AI."""
    b64_json = os.getenv("GOOGLE_CREDENTIALS_BASE64")  # retrieve base64‐encoded key :contentReference[oaicite:9]{index=9}
    if not b64_json:
        raise ValueError("GOOGLE_CREDENTIALS_BASE64 is not set")  # fail early if missing :contentReference[oaicite:10]{index=10}
    decoded = base64.b64decode(b64_json).decode("utf-8")  # decode to JSON text :contentReference[oaicite:11]{index=11}
    creds_info = json.loads(decoded)  # parse JSON into dict :contentReference[oaicite:12]{index=12}
    credentials = service_account.Credentials.from_service_account_info(creds_info)  # create Credentials :contentReference[oaicite:13]{index=13}

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")  # retrieve project ID :contentReference[oaicite:14]{index=14}
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT_ID is not set")  # ensure project is defined :contentReference[oaicite:15]{index=15}

    # Initialize Vertex AI with explicit credentials :contentReference[oaicite:16]{index=16}
    vertexai.init(
        project=project_id,
        location=REGION,
        credentials=credentials
    )


def initialize_pinecone(index_name):
    """Init Pinecone with API key and return the index object."""
    api_key = os.getenv("PINECONE_API_KEY")  # retrieve Pinecone key :contentReference[oaicite:17]{index=17}
    if not api_key:
        raise ValueError("PINECONE_API_KEY is not set")  # fail if missing :contentReference[oaicite:18]{index=18}
    # Create a Pinecone client instance (v3.x+ syntax) :contentReference[oaicite:19]{index=19}
    pc = Pinecone(api_key=api_key)
    return pc.Index(index_name)  # get reference to existing index 


def download_from_s3(bucket, key, client, max_retries=3):
    wait = 1
    for attempt in range(max_retries):
        try:
            resp = client.get_object(Bucket=bucket, Key=key)
            return resp["Body"].read()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(wait)
                wait *= 2
            else:
                raise e


def process_image(image_file, bucket_name, prefix, model, index, total_images, image_index, s3_client, max_retries=5):
    """Download an image from S3, embed via Vertex AI, and upsert to Pinecone."""
    s3_key = f"{prefix}/{image_file}"
    attempt = 0
    while attempt < max_retries:
        try:
            image_bytes = download_from_s3(bucket_name, s3_key, s3_client)
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(image_bytes)
                tmp.flush()
                image = Image.load_from_file(tmp.name)

            embeddings = model.get_embeddings(image=image)  # generate embedding :contentReference[oaicite:23]{index=23}

            print(f"Received embeddings for: {image_file} ({image_index}/{total_images})")

            date_added = datetime.now().isoformat()
            embedding_id = str(uuid.uuid4())

            vector = [
                {
                    'id': embedding_id,
                    'values': embeddings.image_embedding,
                    'metadata': {
                        'date_added': date_added,
                        'file_type': FILE_TYPE,
                        's3_file_path': f"{bucket_name}/{prefix}/",
                        's3_file_name': image_file,
                    }
                }
            ]
            index.upsert(vector)  # upsert to Pinecone 
            print(f"Processed and upserted: {image_file} ({image_index}/{total_images})")
            break
        except Exception as e:
            print(f"Error processing file {image_file}: {e}")
            attempt += 1
            if attempt < max_retries:
                wait_time = 5 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Failed to process file {image_file} after {max_retries} attempts.")


def main(gc_project_id, s3_bucket_name, s3_folder_name, pinecone_index_name):
    # 1) Initialize Vertex AI with service-account credentials :contentReference[oaicite:25]{index=25}
    initialize_vertex_ai()

    # 2) Initialize Pinecone index :contentReference[oaicite:26]{index=26}
    index = initialize_pinecone(pinecone_index_name)

    # 3) Load the multimodal embedding model (1408 dims) :contentReference[oaicite:27]{index=27}
    model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

    # 4) List image files from S3
    s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    resp = s3_client.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_folder_name)
    image_files = [
        obj["Key"].replace(f"{s3_folder_name}/", "")
        for obj in resp.get("Contents", [])
        if obj["Key"].lower().endswith((".jpeg", ".jpg", ".png", ".bmp", ".gif"))
    ]

    total_images = len(image_files)
    if total_images == 0:
        print(f"No images found in s3://{s3_bucket_name}/{s3_folder_name}/")
        return

    # 5) Process images in parallel using threading 
    with ThreadPoolExecutor() as executor:
        futures = []
        for i, image_file in enumerate(image_files):
            futures.append(executor.submit(
                process_image,
                image_file,
                s3_bucket_name,
                s3_folder_name,
                model,
                index,
                total_images,
                i + 1,
                s3_client,
            ))
        for future in as_completed(futures):
            future.result()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate and upsert image embeddings from S3 to Pinecone."
    )
    parser.add_argument('-p', '--project', type=str, required=True,
                        help='Google Cloud project ID.')  # :contentReference[oaicite:30]{index=30}
    parser.add_argument('-b', '--bucket', type=str, required=True,
                        help='S3 bucket name.')
    parser.add_argument('-f', '--folder', type=str, required=True,
                        help='S3 folder containing images.')
    parser.add_argument('-i', '--index', type=str, required=True,
                        help='Pinecone index name.')
    args = parser.parse_args()
    main(args.project, args.bucket, args.folder, args.index)

