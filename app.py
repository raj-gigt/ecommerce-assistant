# Okay, let's convert the functionality to a Flask backend.

# This Flask application will:

# Provide a single endpoint (/recommend) that accepts POST requests.

# Handle file uploads (for the image) and form data (for text queries).

# Use Flask's session to store the conversation history, maintaining context across requests from the same user's browser.

# Call the Gemini API (using the updated gemini-1.5-flash-001 model).

# Process the AI response to ensure it's valid JSON according to your specified format.

# Return the JSON response or an error message.

# Project Structure:

# your_flask_app/
# ├── app.py          # The main Flask application code
# ├── .env            # (Optional, but recommended) for environment variables
# └── requirements.txt # Project dependencies


# 1. requirements.txt:

# Flask>=2.0
# google-generativeai>=0.6.0 # Use a recent version
# Pillow>=9.0
# python-dotenv>=1.0.0 # To load .env file
# IGNORE_WHEN_COPYING_START
# content_copy
# download
# Use code with caution.
# IGNORE_WHEN_COPYING_END

# 2. .env (Optional but Recommended):

# Create a file named .env in the root of your project directory.

# GOOGLE_API_KEY='YOUR_GEMINI_API_KEY'
# # You can also set a secret key for Flask session security here
# FLASK_SECRET_KEY='A_RANDOM_SECRET_KEY_FOR_SESSIONS'
# IGNORE_WHEN_COPYING_START
# content_copy
# download
# Use code with caution.
# Dotenv
# IGNORE_WHEN_COPYING_END

# Replace 'YOUR_GEMINI_API_KEY' with your actual key and 'A_RANDOM_SECRET_KEY_FOR_SESSIONS' with a strong, random string.

# 3. app.py:

from flask import Flask, request, jsonify, session
import google.generativeai as genai
from PIL import Image
import io
import json
import os
from werkzeug.datastructures import FileStorage
from dotenv import load_dotenv # To load environment variables from .env
import re
from flask_cors import CORS  # Import the CORS extension

# Load environment variables from .env file
load_dotenv()

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# IMPORTANT: Set a secret key for session security
# This is required for Flask sessions to work. Get it from environment variable or set a default (less secure)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your_fallback_default_secret_key_CHANGE_THIS')
if app.config['SECRET_KEY'] == 'your_fallback_default_secret_key_CHANGE_THIS' and not os.environ.get('FLASK_SECRET_KEY'):
    print("WARNING: FLASK_SECRET_KEY not set in environment or .env file. Using a default, insecure key.")


# --- AI Model Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    # In a production Flask app, you might exit or raise an exception on startup
    print("Error: GOOGLE_API_KEY environment variable not set. API calls will fail.")
    # For now, we'll allow the app to start but API calls will return errors
genai.configure(api_key=GOOGLE_API_KEY)
# Use the updated model name as suggested by the error
MODEL_NAME = 'gemini-1.5-flash-001' # Or 'gemini-1.5-pro-001'

# Generation configuration for the AI model
generation_config = {
    "temperature": 0.1, # Keep it low for factual responses following instructions
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}

# Note: We don't initialize the model or chat here globally because
# model instances might not be thread-safe, and chat history needs to be
# managed per session/request in a web server context. We'll initialize
# them inside the request handler.
def clean_json_string(json_string: str) -> str:
    # 1. Remove leading/trailing ```json and ```
    cleaned = re.sub(r"^```json\s*|\s*```$", "", json_string.strip(), flags=re.MULTILINE)
    
    # 2. Parse to Python dict
    data = json.loads(cleaned)
    
    # 3. Return pretty‑printed JSON (searchlink stays a plain URL string)
    return json.dumps(data, indent=2)

# --- Helper Function to prepare image for API from FileStorage ---
def get_image_part_from_filestorage(file_storage: FileStorage):
    """Reads an image from Flask FileStorage and prepares it as an API part."""
    try:
        # Read the file content bytes
        img_bytes = file_storage.read()
        # Open image using Pillow from bytes
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')

        # Prepare image data for the API in bytes
        img_byte_arr = io.BytesIO()
        # Use JPEG format for API, adjust quality if needed
        img.save(img_byte_arr, format='JPEG', quality=90)
        img_byte_arr = img_byte_arr.getvalue()

        image_part = {
            "mime_type": "image/jpeg",
            "data": img_byte_arr
        }
        return image_part
    except Exception as e:
        print(f"Error processing image FileStorage: {e}")
        return None

# --- Initial Prompt Text ---
# This detailed prompt sets the rules for the AI
initial_prompt_text = """
You are an AI agent that recommends products on Amazon.in based on user input (images and text).
Your task is:
1.  **Initial Input:** Analyze the provided image and any accompanying text. Identify the main product from the image and its key visual traits. Incorporate any specific requirements from the text input (like price range, brands) into the traits. Generate an Amazon.in search URL using the identified product and traits.
2.  **Subsequent Input:** When the user provides text input *without* an image in a follow-up turn, treat it as a refinement or additional requirement for the *previously identified product and traits*. Update the traits and generate a *new* Amazon.in search URL based on the *updated* traits and the (potentially updated) item name.
3.  **Output Format:** You *must* output only a single JSON object in the following exact format. Do not include any other text, explanation, or formatting outside this JSON object. Ensure the JSON is valid and parseable. **Crucially, do not use any markdown formatting (like backticks) within the JSON values.**
    ```json
    {
    "itemname": "Identified product name (e.g., Men's Jeans)",
    "traits": "Comma-separated list of relevant traits (e.g., Dark Blue, Slim Fit, Rolled Cuffs, Peter England, Price Range 1500-2000)",
    "searchlink": "https://www.amazon.in/s?k=search+query+based+on+itemname+and+traits+with+spaces+replaced+by+plus"
    }
    ```
4.  **Search Link Construction:** The search link should *always* start with `https://www.amazon.in/s?k=` followed by the item name and traits joined by spaces, with *all* spaces replaced by `+`. Do not include any extra parameters unless explicitly requested as a trait that translates to a search parameter (which is unlikely given the format).
5.  **Constraint:** Generate *only* the JSON object. No introductory or concluding text.
6.  **Context:** Remember the conversation history provided in the chat session to understand follow-up text requests. Base updates on the last successful product identification.
"""

# --- Flask Route to handle Recommendations ---
@app.route('/recommend', methods=['POST'])
def recommend_product():
    """
    Handles product recommendation requests. Accepts image file and/or text query.
    Maintains conversation context using Flask session.
    """
    # Get input from the request form
    # request.files is a dictionary of uploaded files
    # request.form is a dictionary of standard form fields
    image_file: FileStorage = request.files.get('image') # Returns FileStorage object or None
    text_query: str = request.form.get('text')           # Returns string or None

    print(f"Received request: image_file={image_file}, text_query='{text_query}'")

    # --- Input Validation ---
    if not image_file and not text_query:
        print("Validation failed: No image or text provided.")
        return jsonify({"error": "No image file or text query provided in the request."}), 400

    # Check if API key is configured
    if not GOOGLE_API_KEY:
         print("Validation failed: API key not set.")
         return jsonify({"error": "Google API key is not configured on the server."}), 500


    # --- Context Management ---
    # Retrieve history from session. Default to empty list if no history exists.
    # Note: The history we stored is a simplified version that doesn't contain
    # the full Content objects that the SDK expects. This is fine for our use case
    # since we're just using it to initialize a new chat session, and the SDK
    # will handle reconstructing the proper objects.
    history = session.get('chat_history', [])
    print(f"Retrieved session history with {len(history)} turns.")

    # --- Prepare Content for API Call ---
    content_parts = []

    # Add the initial prompt *only* for the very first interaction in this session
    if not history:
        content_parts.append(initial_prompt_text)
        print("Added initial prompt to content parts.")

    # Add image part if an image was uploaded in *this* request
    if image_file:
        img_part = get_image_part_from_filestorage(image_file)
        if img_part:
            content_parts.append(img_part)
            print("Added image part from current request to content parts.")
        else:
            print("Failed to process uploaded image.")
            return jsonify({"error": "Failed to process the uploaded image."}), 400 # Bad Request

    # Add text part if text was provided in *this* request
    if text_query:
        content_parts.append(text_query)
        print(f"Added text query '{text_query}' to content parts.")


    # --- Initialize Model and Chat with History ---
    try:
        # Initialize the model and start a chat session with the retrieved history
        model = genai.GenerativeModel(model_name=MODEL_NAME,
                                      generation_config=generation_config)
        chat = model.start_chat(history=history)
        print("AI Model and chat session initialized with history.")

    except Exception as e:
        print(f"Error initializing AI model or chat: {e}")
        return jsonify({"error": f"Failed to initialize AI model: {e}"}), 500


    # --- Send Content to AI and Get Response ---
    try:
        print("Sending message to AI...")
        # Send the current request's content parts. The chat object
        # automatically includes the historical turns before sending.
        response = chat.send_message(content_parts)
        print("Received response from AI.")
    
        # --- Update Context ---
        # Store the *updated* chat history (including the current turn and AI's response)
        # back into the session for the next request.
        # PROBLEM: chat.history contains Content objects that aren't JSON serializable
        # SOLUTION: Store only the text parts of the conversation
        
        # Extract serializable history (just the text parts)
        serializable_history = []
        for turn in chat.history:
            # Each turn has a 'parts' list with the content
            # We'll extract just the text parts for storage
            parts_text = []
            for part in turn.parts:
                # If it's a text part, add it directly
                if isinstance(part, str):
                    parts_text.append(part)
                # If it's an image part, just note that an image was here
                elif isinstance(part, dict) and part.get('mime_type', '').startswith('image/'):
                    parts_text.append("[IMAGE]")
            
            # Store the role and text parts for this turn
            serializable_history.append({
                "role": turn.role,
                "parts": parts_text
            })
        
        # Store the serializable history in the session
        session['chat_history'] = serializable_history
        print(f"Session history updated. Current length: {len(session['chat_history'])}")
    
        # --- Process AI Response ---
        # The AI is instructed to return ONLY JSON. Extract and parse it.
        response_text = response.text.strip() 
        response_text = clean_json_string(response_text)
        print(f"Raw AI response text: {response_text}")
        
        print(type(response_text))

        # Attempt to parse the response text as JSON
        try:
            # Ensure the response looks like a JSON object before parsing
            if response_text.startswith('{') and response_text.endswith('}'):
                print(response_text)
                response_json = json.loads(response_text)

                # Basic validation of the required keys in the JSON
                if all(key in response_json for key in ["itemname", "traits", "searchlink"]):
                    print("Successfully parsed valid JSON response.")
                    return jsonify(response_json), 200 # Return the JSON and 200 OK status
                else:
                    # If JSON is valid but doesn't have expected keys
                    print("Warning: AI returned JSON but structure is invalid.")
                    return jsonify({
                        "error": "AI returned JSON but structure is invalid.",
                        "raw_ai_response": response_text
                    }), 500 # Internal Server Error, or maybe 422 Unprocessable Entity

        except json.JSONDecodeError:
                # If the response text isn't valid JSON
                print(f"Warning: Could not parse response as JSON: {response_text[:200]}...") # Print start of response
                return jsonify({
                    "error": "Could not parse AI response as JSON. AI may not have followed format.",
                    "raw_ai_response": response_text
                }), 500 # Internal Server Error

        except Exception as e:
            # Catch any other errors during response processing
            print(f"An unexpected error occurred while processing AI response: {e}")
            return jsonify({"error": f"Error processing AI response: {e}"}), 500


    except Exception as e:
        # Catch errors during the AI API call itself (network, authentication, rate limits, etc.)
        print(f"An error occurred during AI API call: {e}")
        # Provide a more informative error if possible
        error_message = f"AI API call failed: {e}"
        if "quota" in str(e).lower():
            error_message = "AI API quota exceeded or rate limited."
        elif "api key" in str(e).lower() or "credential" in str(e).lower():
             error_message = "AI API authentication failed. Check your API key."

        return jsonify({"error": error_message}), 500 # Internal Server Error


# --- Run the Flask App ---
if __name__ == '__main__':
    # Use a simple development server.
    # For production, use a WSGI server like Gunicorn or uWSGI.
    # debug=True enables auto-reloading and helpful error pages in development.
    # Disable debug=True in production.
    app.run(debug=True, port=3000) # Run on port 5000
