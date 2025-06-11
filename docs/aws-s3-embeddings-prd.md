# Product Requirements Document (PRD): AWS S3-Hosted Sock Designs Embedding Pipeline

## 1. Purpose
Enable the application to load existing sock-design images from Amazon S3, generate embeddings using the Vertex AI Embeddings API, and store those embeddings in Pinecone—so that all design assets and their vector representations live in AWS and Pinecone, ready for similarity search and downstream features.

## 2. Background & Why
- Current State: A proof-of-concept using Google Cloud Storage (GCS) and Vertex AI embeddings works end-to-end: images are uploaded to GCS, embeddings are generated, and stored in Pinecone.

- Problem: Production image assets now reside in AWS S3; the POC still relies on GCS URIs and GCS-specific config.

- Opportunity: Consolidate storage in AWS S3, update the local terminal script to pull from S3, call Vertex AI embeddings, and push vectors to Pinecone—eliminating cross-cloud complexity and simplifying credential management.

## 3. Scope

In Scope

Script Update

    Modify the existing terminal script to:

        Point at the AWS S3 bucket containing existing images.

        Retrieve image files via AWS SDK (getObject).

        Call Vertex AI Embeddings API for each image.

        Upsert resulting vectors into Pinecone.

Codebase Refactor

    - /api/config.py: Replace GCS-related variables/imports with AWS placeholders (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME).

    - /api/image.py: Swap out GCS URI logic for S3 path construction and getObject calls.

    - Audit entire codebase for any remaining GCS references (imports, helper modules) and refactor to use the new AWS-backed storage interface.

Credential Management

    - Provide a .env.example (or CLI flags) with placeholder AWS credentials and bucket name, to be swapped for real keys once obtained.

Documentation

    - Update README and onboarding guide to document new environment variables, script usage, and credential swap process.

Testing & Validation

    - Validate end-to-end script locally against a sandbox S3 bucket and Pinecone test index.

    - Ensure the number of embeddings in Pinecone matches the count of images in S3.

    - Implement retry logic (3× with exponential backoff) for transient failures.

Out of Scope

    - New image-upload functionality.

    - Migration of legacy images (already in S3).

    - Changes to Pinecone schema beyond storing embeddings.

    - Major AWS infrastructure work (e.g., bucket policy changes beyond read-only access for the script).

## 4. Functional Requirements
    
    1. Configurable AWS S3 Access

        - Support environment variables or CLI flags for:

            - AWS_ACCESS_KEY_ID

            - AWS_SECRET_ACCESS_KEY

            - AWS_REGION

            - S3_BUCKET_NAME

    2. Codebase Updates for AWS Integration

        - Refactor /api/config.py to load AWS credentials and bucket settings instead of GCS parameters.

        - Refactor /api/image.py to build and consume S3 URI paths (e.g., s3://bucket/key) when downloading image data.

        - Identify and replace any remaining google.cloud.storage imports or utilities with AWS SDK equivalents.

    3. Image Retrieval & Embedding Flow

        - Script lists or reads a manifest of image keys from S3_BUCKET_NAME.

        - For each image:

            - Download via getObject.

            - Preprocess/encode as required by Vertex AI.

            - Call Vertex AI Embeddings API (projects/{project}/locations/{location}/embeddings:embed).

            - Receive embedding vector.

            - Upsert vector into Pinecone under the same object key.

    4. Credential Placeholder Swap

        - Supply a .env.example with placeholder values and document the swap process for real AWS credentials.

    5. Testing & Validation

        - Local validation against sandbox S3 bucket and Pinecone test index.

        - Automated check that Pinecone index size equals S3 object count.

        - Logging of errors and retry logic (3× retries with exponential backoff).

## 5. Non-Functional Requirements

    - Security: No hard-coded credentials; use env vars or IAM role. Least-privilege IAM policy scoped to S3 read.

    - Performance: Batch listing of S3 objects; aim for ≥ 5 images/sec embedding throughput.

    - Reliability: Retries on AWS SDK/network errors with exponential backoff; idempotent upserts to Pinecone.

    - Maintainability: Abstract AWS and Vertex AI clients behind simple interfaces; clear logging and error messages.

## 6. User Stories

    - As a developer, I want a single terminal command that pulls all images from S3, generates embeddings via Vertex AI, and upserts them into Pinecone, so I don’t have to juggle multiple scripts or storage platforms.

    - As an ops engineer, I want AWS credentials managed via env vars or IAM roles, so that no secrets are leaked in code.

    - As a QA engineer, I want a sandbox S3 bucket and Pinecone test index to verify embeddings count matches image count before production rollout.

## 7. Dependencies & Assumptions

    Dependencies:

        - AWS SDK (boto3 or aws-sdk)

        - Google Cloud Vertex AI client library

        - Pinecone client library

    Assumptions:

        - Dev team will supply placeholder AWS credentials and later real ones.

        - The S3 bucket contains only images intended for embedding.

        - Pinecone index already exists and matches the expected vector dimensionality.