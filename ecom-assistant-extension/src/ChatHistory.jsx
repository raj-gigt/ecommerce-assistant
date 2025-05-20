import React, { useEffect, useRef } from "react";
import Message from "./Message";

function ChatHistory({ history }) {
  const historyEndRef = useRef(null);

  useEffect(() => {
    if (historyEndRef.current) {
      historyEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [history]);

  return (
    // Add Tailwind classes to the history container
    <div className="flex-grow overflow-y-auto border border-gray-300 p-3 mb-4 bg-gray-50 rounded-md flex flex-col">
      {" "}
      {/* flex-grow, overflow-y-auto, border, p-3, mb-4, bg-gray-50, rounded-md, flex, flex-col */}
      {history.map((message, index) => (
        <Message key={index} message={message} />
      ))}
      <div ref={historyEndRef}></div>
    </div>
  );
}

export default ChatHistory;
