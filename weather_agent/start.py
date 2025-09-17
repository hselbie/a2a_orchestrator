#!/usr/bin/env python3
"""Start script for Weather Agent."""

if __name__ == "__main__":
    from .weather_a2a_server import main
    import asyncio
    asyncio.run(main())