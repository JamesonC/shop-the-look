# Sock Scout

**Sock Scout** is a sample semantic search engine built with Pinecone Serverless and Google's Multimodal Embedding model. It combines text, image and video inputs so you can find past sock inspiration. The project uses a Next.js front end with a FastAPI back end and includes a large royalty‑free dataset for quick demos.

## Features

- **Multimodal search** – query with text, images or video
- **45k demo assets** for instant testing
- **Serverless vector database** powered by Pinecone
- **Deploy locally or on Vercel**
- **Extensible** – customize both the React/Next.js UI and FastAPI server

## Quick Start

### Demo Deployment

Run the sample with preloaded demo assets:

```bash
npx create-pinecone-app@latest --template shop-the-look
```

Then open [http://localhost:3000](http://localhost:3000).

### Full Deployment

1. Clone the repository
2. Install dependencies with `npm install` and `pip install -r requirements.txt`
3. Copy `.env.development.example` to `.env.development` and add your API keys.
   At a minimum you'll need Google Cloud, Pinecone and AWS credentials.
4. Start the servers:

```bash
npm run dev
```

Browse to [http://localhost:3000](http://localhost:3000) to use the app.

### Use Your Own Images

See [scripts/README.md](scripts/README.md) for instructions on embedding and uploading your own images and videos.

## Environment Variables

The application relies on several variables defined in `.env.development`:

- `GOOGLE_CREDENTIALS_BASE64` – base64‑encoded Google Cloud service account
- `GOOGLE_CLOUD_PROJECT_ID` and `GOOGLE_CLOUD_PROJECT_LOCATION`
- `PINECONE_API_KEY` and `PINECONE_INDEX_NAME`
- `PINECONE_TOP_K` – number of results to return
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION`
- `S3_BUCKET_NAME` – S3 bucket where assets are stored
- `NEXT_PUBLIC_DEVELOPMENT_URL` – backend URL when running locally
- `NEXT_PUBLIC_VERCEL_ENV` – set to `development` or `demo`

## Service Notes

- Vercel uploads are limited to 4.5&nbsp;MB per file
- Google Vertex AI analyzes only the first two minutes of video
- Pinecone indexes must use dimension `1408` and cosine metric

## Running Tests

Unit tests are located in the `tests` folder. Run them with:

```bash
pytest -q
```

## Contributing

Contributions are welcome! Please open an issue or pull request.

## License

This project is released under the [MIT License](LICENSE).

## Built With

- [Pinecone](https://www.pinecone.io/)
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai/)
- [Next.js](https://nextjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Vercel](https://vercel.com/)
- [Pexels](https://www.pexels.com/)
