import React from "react";

function Message({ message }) {
  // Determine base classes for a message bubble
  const baseClasses = "mb-2 p-2 rounded-lg max-w-[90%] break-words"; // mb-2, p-2, rounded-lg, max-w-[90%], break-words

  // Conditional classes based on message type and status
  let messageClasses = baseClasses;
  let prefix = "";
  let content = null;

  if (message.type === "user") {
    messageClasses += " bg-green-200 self-end"; // bg-green-200, self-end
    prefix = "You:";
    const { image, text } = message.content;
    content = (
      <>
        {image && (
          <p className="text-sm text-gray-700">Image uploaded ({image.name})</p>
        )}{" "}
        {/* text-sm, text-gray-700 */}
        {text && <p>{text}</p>}
        {!image && !text && <p>(Submitted empty input)</p>}
      </>
    );
  } else if (message.type === "ai") {
    const { status, data, message: errorMessage } = message.content;
    prefix = "AI:";

    if (status === "pending") {
      messageClasses += " bg-gray-300 self-start italic text-gray-700"; // bg-gray-300, self-start, italic, text-gray-700
      content = "Thinking...";
    } else if (status === "error") {
      messageClasses += " bg-red-200 self-start text-red-800 font-semibold"; // bg-red-200, self-start, text-red-800, font-semibold
      prefix = "AI Error:";
      content = errorMessage;
    } else if (status === "cancelled") {
      messageClasses += " bg-gray-300 self-start italic text-gray-700"; // bg-gray-300, self-start, italic, text-gray-700
      prefix = "AI:";
      content = errorMessage; // 'Request cancelled.'
    }
    // Assuming status is 'success' and data is available
    else {
      messageClasses += " bg-blue-200 self-start"; // bg-blue-200, self-start
      const { itemname, traits, searchlink } = data;
      content = (
        <>
          <p className="mb-1">
            <strong className="font-semibold">Item:</strong> {itemname}
          </p>{" "}
          {/* mb-1, font-semibold */}
          <p className="mb-1">
            <strong className="font-semibold">Traits:</strong> {traits}
          </p>{" "}
          {/* mb-1, font-semibold */}
          <p>
            <strong className="font-semibold">Link:</strong>{" "}
            <a
              href={searchlink}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline block break-all"
            >
              {searchlink}
            </a>
          </p>{" "}
          {/* font-semibold, text-blue-600, hover:underline, block, break-all */}
        </>
      );
    }
  }

  // Only render the message bubble if it's a known type
  if (message.type === "user" || message.type === "ai") {
    return (
      <div className={messageClasses}>
        <strong className="mr-1">{prefix}</strong> {/* mr-1 */}
        {content}
      </div>
    );
  }

  return null; // Don't render unknown message types
}

export default Message;
