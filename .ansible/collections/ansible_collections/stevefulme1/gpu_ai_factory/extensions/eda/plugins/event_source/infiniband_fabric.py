"""EDA event source plugin for InfiniBand fabric monitoring."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import asyncio
import json
from datetime import datetime, timezone

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


async def main(queue: asyncio.Queue, args: dict):
    """Monitor InfiniBand fabric for link flaps, congestion, and errors.

    Polls the BCM API or UFM (Unified Fabric Manager) for fabric health
    and emits events when thresholds are exceeded.

    Args:
        queue: The EDA event queue.
        args: Configuration arguments:
            - bcm_url: BCM API endpoint URL
            - bcm_token: API authentication token
            - interval: Polling interval in seconds (default: 30)
            - validate_certs: Whether to validate SSL certs (default: true)
            - link_flap_threshold: Link flap count threshold (default: 3)
            - error_threshold: Error counter threshold (default: 100)
            - congestion_threshold: Congestion percentage threshold
              (default: 80)
    """
    bcm_url = args.get("bcm_url", "").rstrip("/")
    bcm_token = args.get("bcm_token", "")
    interval = int(args.get("interval", 30))
    validate_certs = args.get("validate_certs", True)
    link_flap_threshold = int(args.get("link_flap_threshold", 3))
    error_threshold = int(args.get("error_threshold", 100))
    congestion_threshold = int(args.get("congestion_threshold", 80))

    ssl_context = None if validate_certs else False
    headers = {
        "Authorization": f"Bearer {bcm_token}",
        "Content-Type": "application/json",
    }

    previous_counters = {}

    while True:
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                url = f"{bcm_url}/api/v1/infiniband/fabric"
                async with session.get(url, ssl=ssl_context,
                                       timeout=aiohttp.ClientTimeout(
                                           total=30)) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(interval)
                        continue

                    data = await resp.json()
                    ports = data if isinstance(data, list) else data.get(
                        "ports", data.get("items", []))

                    for port in ports:
                        port_id = port.get("port_id", port.get("guid", ""))
                        now = datetime.now(timezone.utc).isoformat()

                        # Check link flaps
                        link_flaps = port.get("link_flaps", 0)
                        prev = previous_counters.get(port_id, {})
                        prev_flaps = prev.get("link_flaps", 0)
                        if link_flaps - prev_flaps >= link_flap_threshold:
                            await queue.put({
                                "infiniband_fabric": {
                                    "event_type": "link_flap",
                                    "port_id": port_id,
                                    "count": link_flaps - prev_flaps,
                                    "threshold": link_flap_threshold,
                                    "timestamp": now,
                                },
                            })

                        # Check error counters
                        errors = port.get("symbol_errors", 0) + port.get(
                            "link_error_recovery", 0)
                        prev_errors = prev.get("errors", 0)
                        if errors - prev_errors >= error_threshold:
                            await queue.put({
                                "infiniband_fabric": {
                                    "event_type": "error_threshold",
                                    "port_id": port_id,
                                    "error_count": errors - prev_errors,
                                    "threshold": error_threshold,
                                    "timestamp": now,
                                },
                            })

                        # Check congestion
                        utilization = port.get("utilization_percent", 0)
                        if utilization >= congestion_threshold:
                            await queue.put({
                                "infiniband_fabric": {
                                    "event_type": "congestion",
                                    "port_id": port_id,
                                    "utilization_percent": utilization,
                                    "threshold": congestion_threshold,
                                    "timestamp": now,
                                },
                            })

                        # Update counters
                        previous_counters[port_id] = {
                            "link_flaps": link_flaps,
                            "errors": errors,
                        }

        except Exception as exc:
            await queue.put({
                "infiniband_fabric": {
                    "event_type": "error",
                    "error": str(exc),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            })

        await asyncio.sleep(interval)


if __name__ == "__main__":
    import os

    class MockQueue:
        async def put(self, event):
            print(json.dumps(event, indent=2))

    asyncio.run(main(MockQueue(), {
        "bcm_url": os.environ.get("BCM_URL", "https://bcm.example.com"),
        "bcm_token": os.environ.get("BCM_TOKEN", "changeme"),
        "interval": 60,
    }))
