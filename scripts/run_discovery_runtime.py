#!/usr/bin/env python3
"""Run the Agent Business reference discovery service locally."""

from __future__ import annotations

import os
from wsgiref.simple_server import make_server

from service.agent_discovery_runtime import create_app


def main() -> None:
    host = os.environ.get("AGENT_BUSINESS_HOST", "127.0.0.1")
    port = int(os.environ.get("AGENT_BUSINESS_PORT", "8787"))
    app = create_app()
    print(f"Agent Business discovery runtime listening on http://{host}:{port}")
    print("Reference mode emits sanitized JSON-line events to stdout; it is not durable analytics.")
    with make_server(host, port, app) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
