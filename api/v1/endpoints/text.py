import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.config import settings
from api import deps, aws_storage

router = APIRouter()

class TextQuery(BaseModel):
    query: str

@router.post("/search/text")
async def query_text(query: TextQuery):
    try:
        if not query.query:
            raise HTTPException(status_code=400, detail="The query text cannot be empty")

        access_token = settings.get_access_token()

        url, headers, data = settings.get_embedding_request_data(access_token, 'text', query.query)

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        # Extract the first embedding from the response
        embedding_data = response.json()
        vector = embedding_data['predictions'][0]['textEmbedding']

        query_response = deps.index.query(
            vector=vector,
            top_k=settings.k,
            include_metadata=True
        )

        matches = query_response["matches"]
        results = []
        for match in matches:
            meta = match["metadata"]
            s3_name = meta.get("s3_file_name")
            s3_path = meta.get("s3_file_path")
            gcs_name = meta.get("gcs_file_name")
            gcs_path = meta.get("gcs_file_path")

            file_name = s3_name or gcs_name or ""
            file_path = s3_path or gcs_path or settings.s3_bucket_name or ""

            url = ""
            if s3_name or s3_path:
                url = aws_storage.public_url(file_path, file_name)
            if not url and (gcs_name or gcs_path):
                url = f"https://storage.googleapis.com/{gcs_path or ''}{gcs_name or ''}"

            results.append(
                {
                    "score": match["score"],
                    "metadata": {
                        "s3_file_name": file_name,
                        "s3_file_path": file_path,
                        "s3_public_url": url,
                        "file_type": meta.get("file_type"),
                        "segment": meta.get("segment"),
                        "start_offset_sec": meta.get("start_offset_sec"),
                        "end_offset_sec": meta.get("end_offset_sec"),
                        "interval_sec": meta.get("interval_sec"),
                    },
                }
            )

        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
