"""
Video Embedding Generator and Upserter

This script processes videos from an AWS S3 bucket, generates embeddings using Vertex AI, and upserts them to a Pinecone index.

Requirements:
- Python 3.7+
- Google Cloud SDK
- Pinecone account
- Vertex AI API enabled in your Google Cloud project

Required Python packages:
- vertexai
- boto3
- pinecone-client

Usage:
1. Set up environment variables (see below)
2. Run the script with the required arguments

Example:
python video_embedding_processor.py -p your-gc-project-id -b your-s3-bucket-name -f your-s3-folder-name -i your-pinecone-index-name
"""

import argparse
import base64
import os
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import vertexai
from vertexai.vision_models import MultiModalEmbeddingModel, Video
import boto3
from pinecone import Pinecone

# Constants
REGION = 'us-central1'
FILE_TYPE = 'video'
MAX_RETRIES = 5
SUPPORTED_VIDEO_FORMATS = ('mov', 'mp4', 'avi', 'flv', 'mkv', 'mpeg', 'mpg', 'webm', 'wmv')

# Video embedding settings
INTERVAL_SEC = 15
START_OFFSET_SEC = 0
END_OFFSET_SEC = 120

class VideoSegmentConfig:
    def __init__(self, start_offset_sec=None, end_offset_sec=None, interval_sec=None):
        self.start_offset_sec = start_offset_sec
        self.end_offset_sec = end_offset_sec
        self.interval_sec = interval_sec

def setup_google_credentials():
    """Set up Google Cloud credentials from base64-encoded environment variable."""
    google_credentials_base64 = os.getenv('GOOGLE_CREDENTIALS_BASE64')
    if google_credentials_base64:
        credentials_path = '/tmp/google-credentials.json'
        google_credentials = base64.b64decode(google_credentials_base64).decode('utf-8')
        with open(credentials_path, 'w') as f:
            f.write(google_credentials)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    else:
        print("Warning: GOOGLE_CREDENTIALS_BASE64 environment variable not set.")

def download_video_from_s3(bucket, key, client, max_retries=3):
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


def process_video(video_file, bucket_name, prefix, model, index, file_path, video_index, total_videos, s3_client):
    """Process a single video file, generate embeddings, and upsert to Pinecone."""
    s3_key = f"{prefix}/{video_file}"

    for attempt in range(MAX_RETRIES):
        try:
            video_bytes = download_video_from_s3(bucket_name, s3_key, s3_client)
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(video_bytes)
                tmp.flush()
                video = Video.load_from_file(tmp.name)
            video_segment_config = VideoSegmentConfig(
                interval_sec=INTERVAL_SEC,
                start_offset_sec=START_OFFSET_SEC,
                end_offset_sec=END_OFFSET_SEC
            )

            embeddings = model.get_embeddings(
                video=video,
                video_segment_config=video_segment_config,
            )

            print(f"Received embeddings for: {video_file} ({video_index}/{total_videos})")

            for video_embedding in embeddings.video_embeddings:
                vector = [{
                    'id': str(uuid.uuid4()),
                    'values': video_embedding.embedding,
                    'metadata': {
                        'date_added': datetime.now().isoformat(),
                        'file_type': FILE_TYPE,
                        's3_file_path': file_path,
                        's3_file_name': video_file,
                        'segment': video_embedding.start_offset_sec // INTERVAL_SEC,
                        'start_offset_sec': video_embedding.start_offset_sec,
                        'end_offset_sec': video_embedding.end_offset_sec,
                        'interval_sec': video_embedding.end_offset_sec - video_embedding.start_offset_sec,
                    }
                }]
                index.upsert(vector)

            print(f"Processed and upserted: {video_file} ({video_index}/{total_videos})")
            return  # Exit function if successful
        except Exception as e:
            print(f"Error processing file {video_file}: {e}")
            if attempt < MAX_RETRIES - 1:
                wait_time = 5 ** (attempt + 1)  # Exponential backoff
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Failed to process file {video_file} after {MAX_RETRIES} attempts.")

def main(gc_project_id, s3_bucket_name, s3_folder_name, pinecone_index_name):
    """Main function to process videos from S3 and upsert embeddings to Pinecone."""
    setup_google_credentials()

    # Initialize Pinecone
    api_key = os.getenv('PINECONE_API_KEY')
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable is not set.")
    pc = Pinecone(api_key=api_key, source_tag="pinecone:stl_sample_app")
    index = pc.Index(pinecone_index_name)

    # Initialize Vertex AI
    vertexai.init(project=gc_project_id, location=REGION)
    model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

    # List video files in S3 bucket
    s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    resp = s3_client.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_folder_name)
    video_files = [
        obj["Key"].replace(f"{s3_folder_name}/", "")
        for obj in resp.get("Contents", [])
        if obj["Key"].lower().endswith(SUPPORTED_VIDEO_FORMATS)
    ]

    # Process videos in parallel
    total_videos = len(video_files)
    file_path = f'{s3_bucket_name}/{s3_folder_name}/'
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                process_video,
                video_file,
                s3_bucket_name,
                s3_folder_name,
                model,
                index,
                file_path,
                i + 1,
                total_videos,
                s3_client,
            )
            for i, video_file in enumerate(video_files)
        ]
        for future in as_completed(futures):
            future.result()  # This will re-raise any exceptions that occurred during processing

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process videos from an S3 bucket and upsert embeddings to Pinecone.')
    parser.add_argument('-p', '--project', type=str, required=True, help='The Google Cloud project ID.')
    parser.add_argument('-b', '--bucket', type=str, required=True, help='The S3 bucket name.')
    parser.add_argument('-f', '--folder', type=str, required=True, help='The S3 folder containing videos in the bucket.')
    parser.add_argument('-i', '--index', type=str, required=True, help='The Pinecone Index name.')

    args = parser.parse_args()
    main(args.project, args.bucket, args.folder, args.index)

"""
Setup Instructions:

1. Environment Variables:
   Set the following environment variables before running the script:

   a. GOOGLE_CREDENTIALS_BASE64
      Base64-encoded Google Cloud service account key JSON.
      To set this:
      - Get your service account key JSON file
      - Encode it to base64:
        $ base64 -i path/to/your/service-account-key.json | tr -d '\n'
      - Set the environment variable:
        $ export GOOGLE_CREDENTIALS_BASE64="<base64-encoded-string>"

   b. PINECONE_API_KEY
      Your Pinecone API key.
      $ export PINECONE_API_KEY="your-pinecone-api-key"

2. Install required Python packages:
   $ pip install vertexai boto3 pinecone-client

3. Run the script:
   $ python video_embedding_processor.py -p your-gc-project-id -b your-s3-bucket-name -f your-s3-folder-name -i your-pinecone-index-name

   Replace the placeholders with your actual values:
   - your-gc-project-id: Your Google Cloud project ID
   - your-s3-bucket-name: The name of your S3 bucket containing the videos
   - your-s3-folder-name: The folder name within the bucket where videos are stored
   - your-pinecone-index-name: The name of your Pinecone index

Example command:
$ python video_embedding_processor.py -p my-gcp-project -b my-video-bucket -f processed-videos -i my-pinecone-index

Notes:
- Ensure that your Google Cloud service account has the necessary permissions to access Vertex AI.
- The script supports the following video formats: AVI, FLV, MKV, MOV, MP4, MPEG, MPG, WEBM, and WMV.
- The script uses exponential backoff for retrying failed operations, with a maximum of 5 attempts per video.
- Video embedding settings (INTERVAL_SEC, START_OFFSET_SEC, END_OFFSET_SEC) can be adjusted at the top of the script.
"""