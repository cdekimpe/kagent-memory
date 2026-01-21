"""CLI entry point for Kagent Memory service."""

import argparse
import logging
import sys

import uvicorn

from kagent_memory import __version__
from kagent_memory.config import get_settings


def setup_logging(level: str) -> None:
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Kagent Memory - Long-term memory service for Kagent platform",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"kagent-memory {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the memory service")
    serve_parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host to bind to (default: from KAGENT_MEMORY_HOST or 0.0.0.0)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to (default: from KAGENT_MEMORY_PORT or 8080)",
    )
    serve_parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["debug", "info", "warning", "error"],
        help="Log level (default: from KAGENT_MEMORY_LOG_LEVEL or info)",
    )
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    args = parser.parse_args()

    if args.command == "serve":
        settings = get_settings()

        host = args.host or settings.host
        port = args.port or settings.port
        log_level = args.log_level or settings.log_level

        setup_logging(log_level)

        uvicorn.run(
            "kagent_memory.api:create_app",
            factory=True,
            host=host,
            port=port,
            log_level=log_level,
            reload=args.reload,
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
