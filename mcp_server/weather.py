from typing import Any
import httpx
import logging
import sys
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (safe for MCP stdio transport)
logging.basicConfig(
    level=logging.INFO,
    format='[WEATHER-MCP] %(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("weather")
logger.info("Weather MCP server initialized")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    logger.info(f"Making NWS API request to: {url}")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            logger.info(f"NWS API response: {response.status_code} from {response.url}")
            response.raise_for_status()
            data = response.json()
            logger.info(f"NWS API returned data with keys: {list(data.keys()) if data else 'None'}")
            return data
        except Exception as e:
            logger.error(f"NWS API error for {url}: {e}")
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    logger.info(f"get_alerts called with state: {state}")
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        logger.warning(f"No alerts data received for state: {state}")
        return "Unable to fetch alerts or no alerts found."

    features = data["features"]
    logger.info(f"Found {len(features)} alerts for state: {state}")

    if not features:
        logger.info(f"No active alerts for state: {state}")
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in features]
    result = "\n---\n".join(alerts)
    logger.info(f"Returning {len(alerts)} formatted alerts for state: {state}")
    return result

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    logger.info(f"get_forecast called with coordinates: {latitude}, {longitude}")

    # Round coordinates to 4 decimal places as required by NWS API
    lat_rounded = round(latitude, 4)
    lon_rounded = round(longitude, 4)
    logger.info(f"Rounded coordinates to: {lat_rounded}, {lon_rounded}")

    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{lat_rounded},{lon_rounded}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        logger.error(f"Unable to fetch points data for coordinates: {lat_rounded}, {lon_rounded}")
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    if "properties" not in points_data or "forecast" not in points_data["properties"]:
        logger.error(f"No forecast URL in points response for coordinates: {lat_rounded}, {lon_rounded}")
        return "Unable to find forecast endpoint for this location."

    forecast_url = points_data["properties"]["forecast"]
    logger.info(f"Got forecast URL: {forecast_url}")

    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        logger.error(f"Unable to fetch forecast data from: {forecast_url}")
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    if "properties" not in forecast_data or "periods" not in forecast_data["properties"]:
        logger.error("No periods found in forecast response")
        return "No forecast periods available."

    periods = forecast_data["properties"]["periods"]
    logger.info(f"Found {len(periods)} forecast periods, showing first 5")

    forecasts = []
    for i, period in enumerate(periods[:5]):  # Only show next 5 periods
        logger.debug(f"Processing period {i+1}: {period.get('name', 'Unknown')}")
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    result = "\n---\n".join(forecasts)
    logger.info(f"Returning forecast with {len(forecasts)} periods")
    return result

if __name__ == "__main__":
    logger.info("Starting Weather MCP server with stdio transport")
    # Initialize and run the server
    mcp.run(transport='stdio')