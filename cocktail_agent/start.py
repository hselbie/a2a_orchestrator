#!/usr/bin/env python3
"""Start script for Cocktail Agent."""

if __name__ == "__main__":
    import os
    import sys

    # Add parent directory to path to enable imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    import asyncio

    from cocktail_agent.cocktail_a2a_server import main

    asyncio.run(main())
