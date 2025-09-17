from typing import Any, Dict, Optional

import httpx
import logging
import sys
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (safe for MCP stdio transport)
logging.basicConfig(
    level=logging.INFO,
    format='[COCKTAIL-MCP] %(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("cocktaildb")
logger.info("Cocktail MCP server initialized")

# Constants
API_BASE_URL = "https://www.thecocktaildb.com/api/json/v1/1/"


# --- Helper Functions ---
async def make_cocktaildb_request(
    endpoint: str, params: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    """Makes a request to TheCocktailDB API and returns the JSON response."""
    url = f"{API_BASE_URL}{endpoint}"
    logger.info(f"Making CocktailDB API request to: {url} with params: {params}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            logger.info(f"CocktailDB API response: {response.status_code} from {response.url}")
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            data = response.json()

            # The API returns null string instead of null JSON for no results
            if isinstance(data, str) and data.lower() == "null":
                logger.info("CocktailDB API returned null string - no results")
                return None

            # Handle cases where the primary key (drinks/ingredients) might be null
            if data and (
                data.get("drinks") is None and data.get("ingredients") is None
            ):
                # Check if it's a known 'no result' structure or genuinely empty
                if "drinks" in data or "ingredients" in data:
                    logger.info("CocktailDB API returned empty drinks/ingredients")
                    return None  # Explicitly no results found based on API structure

            logger.info(f"CocktailDB API returned data with keys: {list(data.keys()) if data else 'None'}")

            if data:
                drinks_count = len(data.get("drinks", []))
                ingredients_count = len(data.get("ingredients", []))
                logger.info(f"Found {drinks_count} drinks, {ingredients_count} ingredients")

            return data
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error occurred while requesting {e.request.url!r}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return None


def format_cocktail_summary(drink: Dict[str, Any]) -> str:
    """Formats a cocktail dictionary into a readable summary string."""
    return (
        f"ID: {drink.get('idDrink', 'N/A')}\n"
        f"Name: {drink.get('strDrink', 'N/A')}\n"
        f"Category: {drink.get('strCategory', 'N/A')}\n"
        f"Glass: {drink.get('strGlass', 'N/A')}\n"
        f"Alcoholic: {drink.get('strAlcoholic', 'N/A')}\n"
        f"Instructions: {drink.get('strInstructions', 'N/A')[:150]}...\n"
        f"Thumbnail: {drink.get('strDrinkThumb', 'N/A')}"
    )


def format_cocktail_details(drink: Dict[str, Any]) -> str:
    """Formats a cocktail dictionary into a detailed readable string."""
    details = [
        f"ID: {drink.get('idDrink', 'N/A')}",
        f"Name: {drink.get('strDrink', 'N/A')}",
        f"Alternate Name: {drink.get('strDrinkAlternate', 'None')}",
        f"Tags: {drink.get('strTags', 'None')}",
        f"Category: {drink.get('strCategory', 'N/A')}",
        f"IBA Category: {drink.get('strIBA', 'None')}",
        f"Alcoholic: {drink.get('strAlcoholic', 'N/A')}",
        f"Glass: {drink.get('strGlass', 'N/A')}",
        f"Instructions: {drink.get('strInstructions', 'N/A')}",
    ]
    ingredients = []
    for i in range(1, 16):
        ingredient = drink.get(f"strIngredient{i}")
        measure = drink.get(f"strMeasure{i}")
        if ingredient:
            ingredients.append(
                f"- {measure.strip() if measure else ''} {ingredient.strip()}".strip()
            )
    if ingredients:
        details.append("\nIngredients:")
        details.extend(ingredients)

    details.append(f"\nImage URL: {drink.get('strDrinkThumb', 'N/A')}")
    details.append(f"Last Modified: {drink.get('dateModified', 'N/A')}")

    return "\n".join(details)


def format_ingredient(ingredient: Dict[str, Any]) -> str:
    """Formats an ingredient dictionary into a readable string."""
    desc = ingredient.get("strDescription", "No description available.")
    return (
        f"ID: {ingredient.get('idIngredient', 'N/A')}\n"
        f"Name: {ingredient.get('strIngredient', 'N/A')}\n"
        f"Type: {ingredient.get('strType', 'N/A')}\n"
        f"Alcoholic: {ingredient.get('strAlcohol', 'Unknown')}\n"
        f"ABV: {ingredient.get('strABV', 'N/A')}\n"
        f"Description: {desc[:300] + '...' if desc and len(desc) > 300 else desc}"
    )


# --- MCP Tools ---


@mcp.tool()
async def search_cocktail_by_name(name: str) -> str:
    """Searches for cocktails by name.

    Args:
        name: The name of the cocktail to search for (e.g., margarita).
    """
    logger.info(f"search_cocktail_by_name called with name: {name}")
    data = await make_cocktaildb_request("search.php", params={"s": name})

    if data and data.get("drinks"):
        drinks = data["drinks"]
        logger.info(f"Found {len(drinks)} cocktails for name: {name}")
        response_lines = ["Found cocktails:"]
        response_lines.extend([format_cocktail_summary(drink) for drink in drinks])
        result = "\n---\n".join(response_lines)
        logger.info(f"Returning search results for name: {name}")
        return result

    logger.info(f"No cocktails found for name: {name}")
    return "No cocktails found with that name."


@mcp.tool()
async def list_cocktails_by_first_letter(letter: str) -> str:
    """Lists all cocktails starting with a specific letter.

    Args:
        letter: The first letter to search cocktails by (must be a single character).
    """
    logger.info(f"list_cocktails_by_first_letter called with letter: {letter}")

    if len(letter) != 1 or not letter.isalpha():
        logger.warning(f"Invalid letter input: {letter}")
        return "Invalid input: Please provide a single letter."

    data = await make_cocktaildb_request("search.php", params={"f": letter.lower()})

    if data and data.get("drinks"):
        drinks = data["drinks"]
        logger.info(f"Found {len(drinks)} cocktails starting with letter: {letter.upper()}")
        response_lines = [f"Cocktails starting with '{letter.upper()}':"]
        response_lines.extend([format_cocktail_summary(drink) for drink in drinks])
        result = "\n---\n".join(response_lines)
        logger.info(f"Returning cocktails starting with letter: {letter.upper()}")
        return result

    logger.info(f"No cocktails found starting with letter: {letter.upper()}")
    return f"No cocktails found starting with the letter '{letter.upper()}'"


@mcp.tool()
async def search_ingredient_by_name(name: str) -> str:
    """Searches for an ingredient by its name.

    Args:
        name: The name of the ingredient to search for (e.g., vodka).
    """
    logger.info(f"search_ingredient_by_name called with name: {name}")
    data = await make_cocktaildb_request("search.php", params={"i": name})

    if data and data.get("ingredients"):
        ingredient = data["ingredients"][0]  # API returns a list with one item
        logger.info(f"Found ingredient: {ingredient.get('strIngredient', 'Unknown')} for name: {name}")
        result = format_ingredient(ingredient)
        logger.info(f"Returning ingredient info for name: {name}")
        return result

    logger.info(f"No ingredient found for name: {name}")
    return "No ingredient found with that name."


@mcp.tool()
async def list_random_cocktails() -> str:
    """Looks up a single random cocktail."""
    logger.info("list_random_cocktails called")
    data = await make_cocktaildb_request("random.php")

    if data and data.get("drinks"):
        drink = data["drinks"][0]
        cocktail_name = drink.get('strDrink', 'Unknown')
        logger.info(f"Found random cocktail: {cocktail_name}")
        result = format_cocktail_details(drink)
        logger.info(f"Returning random cocktail details for: {cocktail_name}")
        return result

    logger.warning("Could not fetch a random cocktail")
    return "Could not fetch a random cocktail."


@mcp.tool()
async def lookup_cocktail_details_by_id(cocktail_id: str) -> str:
    """Looks up the full details of a specific cocktail by its ID.

    Args:
        cocktail_id: The unique ID of the cocktail.
    """
    logger.info(f"lookup_cocktail_details_by_id called with ID: {cocktail_id}")

    # Validate if cocktail_id is numeric
    if not cocktail_id.isdigit():
        logger.warning(f"Invalid cocktail ID format: {cocktail_id}")
        return "Invalid input: Cocktail ID must be a number."

    data = await make_cocktaildb_request("lookup.php", params={"i": cocktail_id})

    if data and data.get("drinks"):
        drink = data["drinks"][0]
        cocktail_name = drink.get('strDrink', 'Unknown')
        logger.info(f"Found cocktail: {cocktail_name} for ID: {cocktail_id}")
        result = format_cocktail_details(drink)
        logger.info(f"Returning cocktail details for ID: {cocktail_id}")
        return result

    logger.info(f"No cocktail found for ID: {cocktail_id}")
    return f"No cocktail found with ID {cocktail_id}."


# --- Run Server ---
if __name__ == "__main__":
    logger.info("Starting Cocktail MCP server with stdio transport")
    mcp.run(transport="stdio")
