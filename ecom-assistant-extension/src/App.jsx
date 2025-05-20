import React, { useState, useRef, useEffect } from "react";
import RecommendationForm from "./RecommendationForm";
import ChatHistory from "./ChatHistory";

function App() {
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const backendUrl = "http://localhost:3000/recommend";

  const abortControllerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleSubmit = async ({ image, text }) => {
    if (!image && !text) {
      setError("Please provide an image or text query.");
      return;
    }
    // if (!backendUrl) {
    //   setError("Backend URL is not configured.");
    //   console.error("REACT_APP_BACKEND_URL environment variable not set.");
    //   return;
    // }

    setError(null);
    setIsLoading(true);

    const formData = new FormData();
    if (image) {
      formData.append("image", image);
    }
    if (text) {
      formData.append("text", text);
    }

    const userMessage = {
      type: "user",
      content: {
        image: image ? { name: image.name, size: image.size } : null,
        text: text || null,
      },
    };
    const aiPlaceholder = { type: "ai", content: { status: "pending" } };
    setChatHistory((prevHistory) => [
      ...prevHistory,
      userMessage,
      aiPlaceholder,
    ]);
    console.log("User message:", userMessage);
    console.log("AI placeholder:", aiPlaceholder);
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    try {
      const response = await fetch(backendUrl, {
        method: "POST",
        body: formData,
        signal: signal,
      });

      const result = await response.json();

      setChatHistory((prevHistory) => {
        const newHistory = [...prevHistory];
        const lastAiIndex = newHistory.length - 1;

        if (response.ok) {
          newHistory[lastAiIndex] = {
            type: "ai",
            content: { status: "success", data: result },
          };
        } else {
          newHistory[lastAiIndex] = {
            type: "ai",
            content: {
              status: "error",
              message: result.error || `Error: ${response.status}`,
            },
          };
          console.error("Backend error:", response.status, result);
        }
        return newHistory;
      });
    } catch (err) {
      if (err.name === "AbortError") {
        console.log("Fetch request aborted");
        setChatHistory((prevHistory) => {
          const newHistory = [...prevHistory];
          const lastAiIndex = newHistory.length - 1;
          if (newHistory[lastAiIndex].content.status === "pending") {
            newHistory[lastAiIndex] = {
              type: "ai",
              content: { status: "cancelled", message: "Request cancelled." },
            };
          }
          return newHistory;
        });
      } else {
        console.error("Fetch error:", err);
        setError(`An error occurred: ${err.message}`);
        setChatHistory((prevHistory) => {
          const newHistory = [...prevHistory];
          const lastAiIndex = newHistory.length - 1;
          newHistory[lastAiIndex] = {
            type: "ai",
            content: {
              status: "error",
              message: `Fetch failed: ${err.message}`,
            },
          };
          return newHistory;
        });
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    // Add Tailwind classes to the container div
    <div className="flex flex-col h-screen p-4">
      {" "}
      {/* flex-col, h-screen (or max-h-screen), p-4 (padding) */}
      <h1 className="text-xl font-bold mb-4 text-center">
        Amazon Product Recommender
      </h1>{" "}
      {/* text-xl, font-bold, mb-4, text-center */}
      <ChatHistory history={chatHistory} />
      {isLoading && (
        <div className="italic text-gray-600 text-center mb-4">
          Processing...
        </div>
      )}{" "}
      {/* italic, text-gray-600, text-center, mb-4 */}
      {error && (
        <div className="text-red-700 font-bold text-center mb-4">
          Error: {error}
        </div>
      )}{" "}
      {/* text-red-700, font-bold, text-center, mb-4 */}
      <RecommendationForm onSubmit={handleSubmit} isLoading={isLoading} />
    </div>
  );
}

export default App;
