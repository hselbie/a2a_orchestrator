#!/usr/bin/env python3
"""Start script for Cocktail Agent."""

if __name__ == "__main__":
    from .cocktail_a2a_server import main
    import asyncio
    asyncio.run(main())