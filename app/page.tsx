"use client";

// app/page.tsx
import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import videojs from "video.js";
import type VideoJsPlayer from "video.js/dist/types/player";
import "video.js/dist/video-js.css";
import Layout from "./layout";
import "./styles.css";
import { track } from "@vercel/analytics";
import Head from "next/head";

// Components
import {
  PhotoFrameIcon,
  MagnifyingGlassIcon,
  QuestionMarkCircleIcon,
} from "./components/Icons";
import Footer from "./components/Footer";
import { handleFileUpload } from "./components/FileUploadHandler";
import Nav from "./components/Navbar";

const API_URL = (() => {
  switch (process.env.NEXT_PUBLIC_VERCEL_ENV) {
    case "development":
      return process.env.NEXT_PUBLIC_DEVELOPMENT_URL || "http://localhost:8000";
    case "preview":
      return `https://${process.env.NEXT_PUBLIC_VERCEL_URL || ""}`;
    case "production":
      return `https://${process.env.NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL || ""}`;
    case "demo":
      return "https://shop-the-look.sample-app.pinecone.io";
    default:
      return "http://localhost:8000";
  }
})();

interface Result {
  score: number;
  metadata: {
    s3_file_name: string;
    s3_public_url: string;
    s3_file_path: string;
    file_type: "image" | "video" | "text";
    start_offset_sec: number;
    end_offset_sec: number;
    interval_sec: number;
    segment: number;
  };
}

export default function Home() {
  const [query, setQuery] = useState<string>("");
  const [results, setResults] = useState<Result[]>([]);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [dragging, setDragging] = useState<boolean>(false);
  const [totalVectors, setTotalVectors] = useState<number | null>(null);
  const [isSearchComplete, setIsSearchComplete] = useState<boolean>(false);
  const [searchTime, setSearchTime] = useState<number | null>(null);
  const [searchType, setSearchType] = useState<"text" | "image" | "video" | null>(
    null
  );
  const [isInputEmpty, setIsInputEmpty] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoadingResults, setIsLoadingResults] = useState<boolean>(false);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false);

  const suggestions = [
    "Stripes",
    "Clouds",
    "University",
    "America",
    "Surprise me",
  ];
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setIsInputEmpty(false);
    setShowSuggestions(false);
  };

  const clearResults = () => {
    setQuery("");
    setResults([]);
    setIsInputEmpty(true);
    setIsSearchComplete(false);
    setSearchTime(null);
    setSearchType(null);
    setErrorMessage(null);
  };

  const playersRef = useRef<{ [key: string]: VideoJsPlayer }>({});

  const VerticalDivider = () => <div className="h-6 w-px bg-gray-200" />;

  // Scroll-tracking
  useEffect(() => {
    let tracked = false;
    const onScroll = () => {
      const pct =
        (window.scrollY /
          (document.documentElement.scrollHeight - window.innerHeight)) *
        100;
      if (pct > 50 && !tracked) {
        track("scroll_depth", { depth: "50%" });
        tracked = true;
      }
    };
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Page-view analytics
  useEffect(() => {
    const data = {
      timestamp: new Date().toISOString(),
      screenSize: `${window.screen.width}x${window.screen.height}`,
      deviceType: /Mobi|Android/i.test(navigator.userAgent) ? "mobile" : "desktop",
      browserName: navigator.userAgent,
      referrer: document.referrer,
      loadTime: performance.now(),
      language: navigator.language,
      totalVectors,
      appVersion: process.env.NEXT_PUBLIC_APP_VERSION || "unknown",
    };
    track("page_viewed", data);
  }, [totalVectors]);

  // Fetch Pinecone stats
  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API_URL}/api/index/info`);
        setTotalVectors(res.data.total_vectors);
      } catch (e) {
        console.error("Error fetching stats:", e);
      }
    })();
  }, []);

  // Cleanup video.js players
  useEffect(() => {
    return () => {
      Object.values(playersRef.current).forEach((p) =>
        typeof p.dispose === "function" ? p.dispose() : null
      );
      playersRef.current = {};
    };
  }, []);

  // Initialize video.js for results
  useEffect(() => {
    results.forEach((r, i) => {
      if (r.metadata.file_type === "video") {
        const vidId = `video-${i}-${r.metadata.s3_public_url}`;
        const el = document.getElementById(vidId) as HTMLVideoElement;
        if (el && !playersRef.current[vidId]) {
          const player = videojs(el, {
            aspectRatio: "1:1",
            fluid: true,
            controls: true,
            muted: true,
            preload: "auto",
          });
          player.one("ready", () => {
            player.currentTime(r.metadata.start_offset_sec);
          });
          playersRef.current[vidId] = player;
        }
      }
    });
    return () => {
      Object.keys(playersRef.current).forEach((vidId) => {
        if (
          !results.some((_, idx) => `video-${idx}-${results[idx].metadata.s3_public_url}` === vidId)
        ) {
          playersRef.current[vidId].dispose();
          delete playersRef.current[vidId];
        }
      });
    };
  }, [results]);

  const resetSearchState = () => {
    setResults([]);
    setIsSearchComplete(false);
    setSearchTime(null);
    setSearchType(null);
    setErrorMessage(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isInputEmpty) return;
    setShowSuggestions(false);
    resetSearchState();
    setIsSearching(true);
    setSearchType("text");
    setErrorMessage(null);
    setIsLoadingResults(true);
    const start = Date.now();

    try {
      const res = await axios.post(`${API_URL}/api/search/text`, { query });
      setResults(res.data.results);
      setSearchTime(Date.now() - start);
      setIsSearchComplete(true);
      track("search_results", { searchType, query, searchTime });
    } catch (err) {
      console.error("Search error:", err);
      if (axios.isAxiosError(err) && err.response) {
        setErrorMessage(`Oops! ${err.response.data.detail || "Unexpected error."}`);
      } else {
        setErrorMessage("Oops! An unexpected error occurred.");
      }
    } finally {
      setIsSearching(false);
      setIsLoadingResults(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    setIsInputEmpty(!val.trim());
    setShowSuggestions(!!val.trim());
  };

  const handleFileUploadWrapper = async (file: File) => {
    resetSearchState();
    await handleFileUpload(file, {
      API_URL,
      setSearchType,
      setErrorMessage,
      setIsUploading,
      setIsSearchComplete,
      setSearchTime,
      setIsLoadingResults,
      setResults,
      setQuery,
      setIsInputEmpty,
      setIsSearching,
    });
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      track("file_selected");
      await handleFileUploadWrapper(e.target.files[0]);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
  }, []);
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files?.[0]) {
      track("file_dropped");
      await handleFileUploadWrapper(e.dataTransfer.files[0]);
    }
  };

  return (
    <Layout>
      <Head>
        <title>Sock Scout</title>
      </Head>

      <div
        className={`relative flex flex-col items-center min-h-screen bg-white ${dragging ? "border-4 border-dashed border-blue-500" : ""
          }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Global nav */}
        <Nav />

        {/* Hero / search */}
        <div className="w-full bg-white pb-8 border-gray-200">
          <div className="max-w-6xl mx-auto px-4 md:px-0 mt-12 text-center space-y-6">
            <h1 className="text-5xl md:text-6xl font-bold text-[#171111]">
              Find Client-Winning Sock Inspiration
            </h1>
            <p className="text-xl font-medium text-gray-700">
              Uncover the perfect past sock inspiration using AI search by tet or 
              image, to fit any client's needs.
            </p>

            <div className="max-w-xl mx-auto mt-6 relative">
              <form onSubmit={handleSubmit} className="flex items-center">
                <div className="flex-grow flex items-center bg-white rounded shadow border">
                  <input
                    type="text"
                    value={query}
                    onChange={handleInputChange}
                    onFocus={() => setShowSuggestions(true)}
                    onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                    placeholder="Describe the sock or drag in an image"
                    className="w-full px-6 py-3 text-gray-700 focus:outline-none"
                    disabled={isUploading || isSearching}
                  />
                  {!isInputEmpty && (
                    <>
                      <button
                        type="button"
                        onClick={clearResults}
                        className="text-gray-400 hover:text-gray-600 px-2 focus:outline-none"
                      >
                        ×
                      </button>
                      <VerticalDivider />
                    </>
                  )}
                  <label
                    htmlFor="upload-input"
                    className={`cursor-pointer px-4 ${isUploading || isSearching
                        ? "text-gray-400"
                        : "text-gray-500 hover:text-gray-700"
                      }`}
                  >
                    <PhotoFrameIcon className="h-6 w-6" />
                  </label>
                </div>
                <input
                  id="upload-input"
                  type="file"
                  accept="image/*,video/*"
                  onChange={handleFileChange}
                  className="hidden"
                  disabled={isUploading || isSearching}
                />
                <button
                  type="submit"
                  className={`ml-2 p-2 focus:outline-none ${isInputEmpty
                      ? "text-gray-400 cursor-not-allowed"
                      : "text-red-600 hover:text-red-700"
                    }`}
                  disabled={isInputEmpty || isUploading || isSearching}
                >
                  <MagnifyingGlassIcon className="h-6 w-6" />
                </button>
              </form>

              {/* Suggestions */}
              {showSuggestions && suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white border rounded shadow-lg z-10">
                  {suggestions.map((s, i) => (
                    <div
                      key={i}
                      className="px-4 py-2 hover:bg-gray-100 cursor-pointer flex items-center"
                      onClick={() => handleSuggestionClick(s)}
                    >
                      <MagnifyingGlassIcon className="h-4 w-4 mr-2 text-red-600" />
                      {s}
                    </div>
                  ))}
                </div>
              )}

              {/* Error or loading */}
              {errorMessage && <div className="mt-4 text-red-500">{errorMessage}</div>}
              {(isUploading || isSearching) && (
                <div className="mt-4 text-gray-600">
                  {isUploading
                    ? "Uploading, embedding, and searching..."
                    : "Searching..."}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="w-full bg-white pt-6">
          <div className="max-w-6xl mx-auto px-4 md:px-0">
            {isSearchComplete && totalVectors !== null && (
              <div className="mb-4 text-gray-700 flex items-center">
                <span>
                  Searched {totalVectors.toLocaleString()} styles{" "}
                  {searchType === "text" && <>for <strong>{query}</strong></>}
                  {searchType === "image" && <>for your image</>}
                  {searchType === "video" && <>for your video</>}
                </span>
                <button
                  onClick={clearResults}
                  className="ml-2 text-gray-400 hover:text-gray-600 focus:outline-none"
                >
                  ×
                </button>
              </div>
            )}

            {isLoadingResults ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {Array.from({ length: 12 }).map((_, i) => (
                  <div key={i} className="animate-pulse bg-gray-200 h-64 rounded" />
                ))}
              </div>
            ) : (
              results.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {results.map((r, i) => {
                    const key = `result-${i}`;
                    const url = r.metadata.s3_public_url;
                    console.log(`Result ${i} URL:`, url);

                    return (
                      <div
                        key={key}
                        className="
                          group 
                          bg-white 
                          p-2 
                          rounded-lg 
                          transition-transform transition-shadow 
                          hover:-translate-y-1 hover:shadow-lg
                        "
                      >
                        {r.metadata.file_type === "image" ? (
                          <img
                            src={url}
                            alt={r.metadata.s3_file_name}
                            className="w-full h-auto object-cover rounded-md"
                          />
                        ) : (
                          <video
                            className="w-full rounded-md"
                            controls
                            preload="metadata"
                            id={`video-${i}`}
                          >
                            <source src={url} type="video/mp4" />
                          </video>
                        )}

                        <div className="mt-2 text-sm text-gray-600 flex items-center">
                          Similarity score: {r.score.toFixed(4)}
                          <div className="relative ml-1 group">
                            <QuestionMarkCircleIcon className="h-4 w-4 text-gray-400 group-hover:text-gray-600" />
                            <div className="
                              absolute 
                              bot tom-full 
                              left-1/2 
                              transform -translate-x-1/2 
                              mb-1 
                              bg-gray-700 
                              text-white 
                              text-xs 
                              rounded 
                              py-1 px-2 
                              whitespace-nowrap 
                              hidden 
                              group-hover:block
                              ">
                              Cosine similarity score between 0–1, higher is more similar.{' '}
                              <a
                                href="https://www.pinecone.io/learn/vector-similarity"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="underline ml-1"
                              >
                                Learn more
                              </a>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )
            )}
          </div>
        </div>

        <Footer />
      </div>
    </Layout>
  );
}