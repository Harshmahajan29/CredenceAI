"""
run.py — robust launcher for a FastAPI app served by Uvicorn.

Features:
- Windows Proactor event loop policy when needed
- Optional uvloop on Unix for better performance
- CLI / env var configuration for host, port, reload, log level
- Structured logging setup
- Graceful shutdown on SIGINT/SIGTERM
"""
import os
import sys
import signal
import argparse
import asyncio
import logging

# Windows: ensure ProactorEventLoop for subprocess/IO compatibility
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

# Try to use uvloop on Unix for better throughput (optional)
if sys.platform != "win32":
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except Exception:
        pass

import uvicorn

DEFAULT_HOST = os.getenv("APP_HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("APP_PORT", "8000"))
DEFAULT_RELOAD = os.getenv("APP_RELOAD", "false").lower() in ("1", "true", "yes")
DEFAULT_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "info")

def configure_logging(level: str) -> None:
    level = level.upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # uvicorn loggers
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)

def parse_args():
    p = argparse.ArgumentParser(description="Run Uvicorn server for app.main:app")
    p.add_argument("--host", default=DEFAULT_HOST, help="Host to bind to")
    p.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind to")
    p.add_argument("--reload", action="store_true", default=DEFAULT_RELOAD, help="Enable autoreload (dev only)")
    p.add_argument("--log-level", default=DEFAULT_LOG_LEVEL, help="Logging level")
    p.add_argument("--workers", type=int, default=1, help="Number of worker processes (use Gunicorn for >1)")
    p.add_argument("--app", default="app.main:app", help="ASGI app import path")
    return p.parse_args()

async def _run_uvicorn(config: uvicorn.Config):
    server = uvicorn.Server(config)
    # Run server until stopped; server.serve() is a coroutine
    await server.serve()

def main():
    args = parse_args()
    configure_logging(args.log_level)
    logger = logging.getLogger("run")

    # Recommend using Gunicorn for multiple workers in production
    if args.workers != 1:
        logger.warning("Using multiple workers from this script is not recommended. "
                       "Use Gunicorn with uvicorn.workers.UvicornWorker for production.")
    logger.info("Starting server", extra={"host": args.host, "port": args.port, "reload": args.reload})

    config = uvicorn.Config(
        app=args.app,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload,
        # limit_concurrency, timeout_keep_alive, etc. can be tuned here
    )

    loop = asyncio.get_event_loop()

    # Graceful shutdown handling
    stop_event = asyncio.Event()

    def _signal_handler(signum, frame):
        logger.info("Received signal to stop", extra={"signal": signum})
        # schedule stop in event loop
        loop.call_soon_threadsafe(stop_event.set)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _signal_handler)
        except Exception:
            # Some platforms (Windows) may not allow setting all signals
            pass

    async def _main():
        # Run server and wait for stop_event
        server_task = asyncio.create_task(_run_uvicorn(config))
        await stop_event.wait()
        logger.info("Shutting down server gracefully...")
        # uvicorn.Server.serve() will exit when loop stops; give it a moment
        # Cancel server task if still running
        if not server_task.done():
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass

    try:
        loop.run_until_complete(_main())
    except Exception as e:
        logger.exception("Server crashed", exc_info=e)
    finally:
        logger.info("Server stopped")

if __name__ == "__main__":
    main()
