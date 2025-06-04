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
3. Copy `.env.development.example` to `.env.development` and set your Google Cloud and Pinecone keys
4. Start the servers:

```bash
npm run dev
```

Browse to [http://localhost:3000](http://localhost:3000) to use the app.

### Use Your Own Images

See [scripts/README.md](scripts/README.md) for instructions on embedding and uploading your own images and videos.

## Service Notes

- Vercel uploads are limited to 4.5&nbsp;MB per file
- Google Vertex AI analyzes only the first two minutes of video
- Pinecone indexes must use dimension `1408` and cosine metric

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
