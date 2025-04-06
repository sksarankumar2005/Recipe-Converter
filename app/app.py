"""
Flask application for Recipe Converter.
This script initializes the Flask app and defines routes.
"""
from flask import Flask, request, render_template, jsonify
from recipe_scrapers import scrape_me
import recipeconverter as rc

app = Flask(__name__)
app.config.from_object(__name__)
app.config["SECRET_KEY"] = "7d441f27d441f28567d441fb6176a"


@app.route("/", methods=["GET"])
def hello():
    """
    Renders the form.html template.

    Returns:
        Response: The rendered HTML template for the form page.
    """
    return render_template("form.html")


@app.route("/convert", methods=["POST"])
def convert():
    """
    Handle a POST request to convert a recipe based on a multiplier.

    This function expects a JSON payload with the following structure:
    {
        "data": <string>,        # The recipe text to be converted.
        "multiplier": <number>   # The multiplier to adjust the recipe quantities.
    }

    Returns:
        Response: A JSON response with the converted recipe or an error message.
        - On success: {"data": <converted_recipe>}
        - On failure: {"error": <error_message>} with an appropriate HTTP status code.

    Errors:
        - 400 Bad Request: If the JSON payload is invalid, missing required fields,
        or if the multiplier is not a valid number.
    """
    response = request.get_json()
    if not response:
        return jsonify({"error": "Invalid JSON data"}), 400

    recipe = rc.RecipeConverter()
    text = response.get("data")
    multiplier = response.get("multiplier")

    if not text or not multiplier:
        return jsonify({"error": "Missing 'data' or 'multiplier' in request"}), 400

    try:
        multiplier = float(multiplier)
    except ValueError:
        return jsonify({"error": "'multiplier' must be a number"}), 400

    return jsonify({"data": recipe.convert_recipe(text, multiplier)})


@app.route("/ingredients_from_url", methods=["POST"])
def ingredients_from_url():
    """
    Extracts ingredients and instructions from a recipe URL provided in a JSON request.

    The function expects a JSON payload with a key "url" containing the recipe URL.
    It uses a web scraper to extract the ingredients and instructions from the recipe page.

    Returns:
        - A JSON response containing:
        - "ingredients": A string of ingredients separated by newlines.
        - "instructions": A string of instructions with double newlines separating steps.
        - If input JSON is invalid or the URL is missing,returns400 error with appropriate message
        - If scraping the URL fails, returns a 400 error with the exception message.
    """
    response = request.get_json()
    if not response:
        return jsonify({"error": "Invalid JSON data"}), 400

    url = response.get("url")
    if not url:
        return jsonify({"error": "Missing 'url' in request"}), 400

    try:
        scraper = scrape_me(url)
    except (ValueError, AttributeError) as e:
        return jsonify({"error": f"Failed to scrape the URL: {str(e)}"}), 400

    return jsonify({
        "ingredients": "\n".join(scraper.ingredients()),
        "instructions": scraper.instructions().replace("\n", "\n\n")
    })


if __name__ == "__main__":
    app.run(debug=False)
