"""
Culina AI - Flask Backend

Routes:
    GET  /          -> Chat UI
    POST /api/chat  -> Gemini AI chat

API key is loaded from .env / environment variable.
The API key is NEVER sent to the frontend.
"""

import os
import logging

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import (
    CHATBOT_TITLE,
    GEMINI_MODEL,
    MAX_HISTORY_MESSAGES,
    MAX_MESSAGE_LENGTH,
    SYSTEM_PROMPT,
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

# Always load .env from the same folder where app.py exists.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)


# ============================================================
# GEMINI API KEY
# ============================================================

API_KEY = os.getenv("GEMINI_API_KEY")


if API_KEY:
    logger.info("GEMINI_API_KEY loaded successfully.")
else:
    logger.error(
        "GEMINI_API_KEY was NOT found. "
        "Please check your .env file."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

_client = None


def get_client():
    """
    Create Gemini client only when required.
    """

    global _client

    if _client is None:

        if not API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured on the server."
            )

        _client = genai.Client(
            api_key=API_KEY
        )

    return _client


# ============================================================
# VALID ROLES
# ============================================================

VALID_ROLES = {
    "user",
    "assistant"
}


# ============================================================
# PROFESSIONAL AI INSTRUCTIONS
# ============================================================

PROFESSIONAL_SYSTEM_PROMPT = """
You are Culina AI, a premium professional Catering Assistant
and Cooking Consultant.

Your role is to provide practical, professional and easy-to-follow
guidance for cooking, recipes and catering.

You can help with:

- Cooking recipes
- Step-by-step cooking instructions
- Indian cuisine
- International cuisine
- Vegetarian dishes
- Non-vegetarian dishes
- Catering menu planning
- Wedding catering
- Corporate catering
- Event catering
- Guest quantity calculations
- Portion planning
- Ingredient calculations
- Food preparation
- Kitchen planning
- Catering staff planning
- Food service planning
- Dietary requirements
- Budget-friendly catering


============================================================
GENERAL RESPONSE STYLE
============================================================

Always answer like an experienced professional chef
and catering consultant.

Keep answers:

- Clear
- Professional
- Practical
- Structured
- Easy to scan
- Mobile friendly

Avoid long unstructured paragraphs.

Use clear section titles.

Use numbered steps for procedures.

Use "-" for lists.

Do not use unnecessary emojis.


============================================================
IMPORTANT FORMATTING
============================================================

Do NOT use Markdown heading symbols.

Never use:

#
##
###
####
#####

Do not use "*" for normal bullet points.

Use "-" for simple lists.

Use numbered steps for cooking procedures.

Do not create huge paragraphs.

Keep sections separated with blank lines.

Do not repeat information unnecessarily.

Do not use raw Markdown formatting.


============================================================
RECIPE FORMAT
============================================================

When the user asks for a recipe or asks:

"How to make..."

Use this structure:


DISH NAME


Overview

Give a short professional description of the dish.


Ingredients

- Ingredient — quantity
- Ingredient — quantity
- Ingredient — quantity
- Ingredient — quantity


Preparation

1. Explain the preparation clearly.
2. Explain the next preparation step.
3. Continue as needed.


Step-by-Step Cooking Method

1. Explain exactly what to do first.
2. Explain the next cooking step.
3. Mention flame level when useful.
4. Mention temperature when useful.
5. Mention cooking time when useful.
6. Continue until the dish is completely prepared.


Cooking Time

Preparation Time: X minutes
Cooking Time: X minutes
Total Time: X minutes


Serving Suggestions

Explain how the dish should be served and
what accompaniments work well.


Professional Tips

- Give a useful chef-level tip.
- Give a practical cooking tip.
- Mention a common mistake to avoid.
- Give a catering tip when relevant.


============================================================
CATERING FORMAT
============================================================

For catering questions, use:


Requirement

Clearly identify the requirement.


Recommended Plan

Give the recommended catering approach.


Recommended Menu

List the suggested dishes.


Quantity / Portions

Give quantities based on guest count.


Preparation Plan

Explain what should be prepared in advance.


Execution Steps

1. Preparation
2. Cooking
3. Holding
4. Service
5. Cleanup


Professional Tips

Give practical professional catering recommendations.


============================================================
GUEST QUANTITY CALCULATIONS
============================================================

When the user gives a guest count, calculate quantities
based on the number of guests.

Always mention:

Number of Guests:
Recommended Quantity:
Suggested Buffer:
Final Estimated Quantity:

If the exact quantity depends on serving style,
clearly state the assumption.

Example:

Assumption:
This quantity is calculated for buffet-style service
for approximately 50 guests.


============================================================
MENU PLANNING
============================================================

For menu planning requests, use:

Event Type

Guest Count

Recommended Menu

Starters

Main Course

Side Dishes

Dessert

Beverages

Quantity Guidance

Professional Tips


============================================================
COOKING INSTRUCTIONS
============================================================

When giving cooking instructions:

- Keep each step short.
- Keep steps in logical order.
- Mention cooking time where useful.
- Mention flame level where useful.
- Mention temperature where useful.
- Mention resting time where useful.
- Mention preparation time where useful.
- Avoid unnecessary repetition.


============================================================
ASSUMPTIONS
============================================================

If the user does not provide enough information,
make a reasonable assumption.

Clearly state the assumption.

Never pretend that missing information is known.


============================================================
FOOD SAFETY
============================================================

Provide sensible food-safety guidance when relevant.

Pay attention to:

- Proper cooking
- Safe storage
- Temperature control
- Cross-contamination
- Raw and cooked food separation


============================================================
FINAL QUALITY CHECK
============================================================

Before responding, check:

1. Is the answer professional?
2. Is it structured?
3. Are the steps in logical order?
4. Are quantities clear?
5. Are cooking times included when relevant?
6. Is the answer practical?
7. Are raw Markdown heading symbols removed?
8. Are unnecessary asterisks removed?
9. Is the response easy to read?
10. Does it answer the user's actual question?

Always prioritize clarity and usefulness.
"""


# ============================================================
# COMBINE EXISTING SYSTEM PROMPT + PROFESSIONAL PROMPT
# ============================================================

FINAL_SYSTEM_PROMPT = f"""
{SYSTEM_PROMPT}

------------------------------------------------------------

{PROFESSIONAL_SYSTEM_PROMPT}
"""


# ============================================================
# VALIDATE USER MESSAGE
# ============================================================

def validate_message(message):
    """
    Validate incoming user message.

    Returns:
        (True, None)
        OR
        (False, error_message)
    """

    if message is None:
        return False, "Field 'message' is required."

    if not isinstance(message, str):
        return False, "Field 'message' must be a string."

    stripped = message.strip()

    if not stripped:
        return False, "Field 'message' cannot be empty."

    if len(stripped) > MAX_MESSAGE_LENGTH:
        return (
            False,
            f"Field 'message' exceeds the maximum length "
            f"of {MAX_MESSAGE_LENGTH} characters."
        )

    return True, None


# ============================================================
# SANITIZE CONVERSATION HISTORY
# ============================================================

def sanitize_history(history):
    """
    Validate and clean conversation history.

    Expected format:

    [
        {
            "role": "user",
            "content": "Hello"
        },
        {
            "role": "assistant",
            "content": "Hello! How can I help?"
        }
    ]
    """

    if history is None:
        return []

    if not isinstance(history, list):
        return []

    cleaned = []

    for item in history:

        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if role not in VALID_ROLES:
            continue

        if not isinstance(content, str):
            continue

        content = content.strip()

        if not content:
            continue

        if len(content) > MAX_MESSAGE_LENGTH:
            content = content[:MAX_MESSAGE_LENGTH]

        cleaned.append(
            {
                "role": role,
                "content": content
            }
        )

    # Keep only recent messages.
    if len(cleaned) > MAX_HISTORY_MESSAGES:
        cleaned = cleaned[-MAX_HISTORY_MESSAGES:]

    return cleaned


# ============================================================
# BUILD GEMINI CONTENTS
# ============================================================

def build_gemini_contents(history, message):
    """
    Convert our conversation history to Google GenAI format.
    """

    role_map = {
        "user": "user",
        "assistant": "model"
    }

    contents = []

    for turn in history:

        contents.append(
            types.Content(
                role=role_map[turn["role"]],
                parts=[
                    types.Part.from_text(
                        text=turn["content"]
                    )
                ]
            )
        )

    # Add current user message.
    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=message
                )
            ]
        )
    )

    return contents


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/", methods=["GET"])
def index():

    return render_template(
        "index.html",
        chatbot_title=CHATBOT_TITLE
    )


# ============================================================
# CHAT API
# ============================================================

@app.route("/api/chat", methods=["POST"])
def chat():

    # --------------------------------------------------------
    # Check JSON
    # --------------------------------------------------------

    if not request.is_json:

        return jsonify(
            {
                "error": "Request body must be JSON."
            }
        ), 400

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):

        return jsonify(
            {
                "error": "Invalid JSON payload."
            }
        ), 400

    # --------------------------------------------------------
    # Validate message
    # --------------------------------------------------------

    message = data.get("message")

    is_valid, error_message = validate_message(
        message
    )

    if not is_valid:

        return jsonify(
            {
                "error": error_message
            }
        ), 400

    # --------------------------------------------------------
    # History
    # --------------------------------------------------------

    history = sanitize_history(
        data.get("history")
    )

    message = message.strip()

    # --------------------------------------------------------
    # Gemini client
    # --------------------------------------------------------

    try:

        client = get_client()

    except RuntimeError as exc:

        logger.error(
            "Gemini client not configured: %s",
            exc
        )

        return jsonify(
            {
                "error": (
                    "The chatbot is not configured correctly. "
                    "Please check your GEMINI_API_KEY configuration."
                )
            }
        ), 500

    # --------------------------------------------------------
    # Generate response
    # --------------------------------------------------------

    try:

        contents = build_gemini_contents(
            history,
            message
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=FINAL_SYSTEM_PROMPT,
                temperature=0.7,
            )
        )

        reply = (
            response.text or ""
        ).strip()

        if not reply:

            reply = (
                "I'm sorry, I wasn't able to generate a response. "
                "Could you rephrase your question?"
            )

    except Exception as exc:

        logger.exception(
            "Error while generating Gemini response: %s",
            exc
        )

        return jsonify(
            {
                "error": (
                    "Something went wrong while generating "
                    "a response. Please try again."
                )
            }
        ), 502

    # --------------------------------------------------------
    # Return response
    # --------------------------------------------------------

    return jsonify(
        {
            "reply": reply
        }
    ), 200


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(_error):

    return jsonify(
        {
            "error": "Not found."
        }
    ), 404


@app.errorhandler(405)
def method_not_allowed(_error):

    return jsonify(
        {
            "error": "Method not allowed."
        }
    ), 405


@app.errorhandler(500)
def server_error(_error):

    return jsonify(
        {
            "error": "Internal server error."
        }
    ), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    logger.info("Starting Culina AI...")
    logger.info(
        "Environment file: %s",
        ENV_FILE
    )

    if API_KEY:
        logger.info("Gemini API key detected.")
    else:
        logger.error(
            "Gemini API key NOT detected."
        )

    app.run(
        debug=False,
        host="0.0.0.0",
        port=5000
    )