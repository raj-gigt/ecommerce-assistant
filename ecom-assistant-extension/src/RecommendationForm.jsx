import React, { useState, useRef } from "react";

const RecommendationForm = ({ onSubmit, isLoading }) => {
  const [imageFile, setImageFile] = useState(null);
  const [textQuery, setTextQuery] = useState("");
  const fileInputRef = useRef(null);

  const handleImageChange = (event) => {
    const file = event.target.files[0];
    setImageFile(file);
  };

  const handleTextChange = (event) => {
    setTextQuery(event.target.value);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit({ image: imageFile, text: textQuery.trim() });
    setImageFile(null);
    setTextQuery("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    // Add Tailwind classes to the form
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 border-t pt-4">
      {" "}
      {/* flex-col, gap-4, border-t, pt-4 */}
      <div className="form-group">
        {" "}
        {/* Optional wrapper div */}
        <label htmlFor="imageFile" className="font-bold block mb-1">
          Upload Image:
        </label>{" "}
        {/* font-bold, block, mb-1 */}
        <input
          type="file"
          id="imageFile"
          accept="image/*"
          onChange={handleImageChange}
          ref={fileInputRef}
          disabled={isLoading}
          className="w-full text-sm text-gray-500
                     file:mr-4 file:py-2 file:px-4
                     file:rounded-md file:border-0
                     file:text-sm file:font-semibold
                     file:bg-blue-50 file:text-blue-700
                     hover:file:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
        />
        {imageFile && (
          <span className="block text-sm text-gray-600 mt-1 break-all">
            {imageFile.name}
          </span>
        )}{" "}
        {/* block, text-sm, text-gray-600, mt-1, break-all */}
      </div>
      <div className="form-group">
        {" "}
        {/* Optional wrapper div */}
        <label htmlFor="textQuery" className="font-bold block mb-1">
          Text Query:
        </label>{" "}
        {/* font-bold, block, mb-1 */}
        <input
          type="text"
          id="textQuery"
          value={textQuery}
          onChange={handleTextChange}
          placeholder="e.g., price range 1500-2000, brand Peter England"
          disabled={isLoading}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring focus:border-blue-300 disabled:opacity-50 disabled:cursor-not-allowed" // w-full, padding, border, rounded, focus styles, disabled styles
        />
      </div>
      <button
        type="submit"
        disabled={isLoading || (!imageFile && textQuery.trim() === "")}
        className="w-full py-2 px-4 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 focus:outline-none focus:ring focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed" // width, padding, background, text, font, rounded, hover, focus, disabled styles
      >
        {isLoading ? "Processing..." : "Search"}
      </button>
    </form>
  );
};

export default RecommendationForm;
