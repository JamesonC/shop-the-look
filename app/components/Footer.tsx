import React from 'react';

const Footer: React.FC = () => {
  return (
    <div className="w-full mt-auto py-4 text-center text-gray-500 text-sm">
      <p>
        Built with{' '}
        <a
          href="https://www.pinecone.io/?utm_source=shop-the-look&utm_medium=referral"
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-800 hover:underline"
        >
          Pinecone
        </a>
        ,{' '}
        <a
          href="https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-multimodal-embeddings"
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-800 hover:underline"
        >
          Google Multimodal VertexAI Embedding Model
        </a>
        , and{' '}
        <a
          href="https://cloud.google.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-800 hover:underline"
        >
          Google Cloud
        </a>
        .
      </p>
      <p className="mt-2">
        Made with <span className="text-red-500">❤️</span> by Sock Club Labs.
      </p>
    </div>
  );
};

export default Footer;
