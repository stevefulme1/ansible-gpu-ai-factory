"""EDA event source plugin for DGX telemetry via Redfish/IPMI."""

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
    """Stream DGX health telemetry via Redfish API.

    Monitors temperature, power consumption, GPU errors, ECC errors,
    and fan speed from DGX systems and emits events to the EDA queue.

    Args:
        queue: The EDA event queue.
        args: Configuration arguments:
            - hosts: List of DGX BMC addresses
            - username: Redfish/IPMI username
            - password: Redfish/IPMI password
            - interval: Polling interval in seconds (default: 30)
            - validate_certs: Whether to validate SSL certs (default: true)
            - metrics: List of metrics to collect (default: all)
              Options: temperature, power, gpu_errors, ecc_errors, fan_speed
    """
    hosts = args.get("hosts", [])
    username = args.get("username", "")
    password = args.get("password", "")
    interval = int(args.get("interval", 30))
    validate_certs = args.get("validate_certs", True)
    metrics = args.get("metrics", [
        "temperature", "power", "gpu_errors", "ecc_errors", "fan_speed",
    ])

    ssl_context = None if validate_certs else False

    while True:
        for host in hosts:
            base_url = f"https://{host}" if not host.startswith("http") else host
            auth = aiohttp.BasicAuth(username, password)

            try:
                async with aiohttp.ClientSession(auth=auth) as session:
                    telemetry = {"host": host, "timestamp": datetime.now(
                        timezone.utc).isoformat()}

                    if "temperature" in metrics:
                        url = f"{base_url}/redfish/v1/Chassis/1/Thermal"
                        async with session.get(url, ssl=ssl_context,
                                               timeout=aiohttp.ClientTimeout(
                                                   total=15)) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                temps = []
                                for t in data.get("Temperatures", []):
                                    temps.append({
                                        "name": t.get("Name", ""),
                                        "reading_celsius": t.get(
                                            "ReadingCelsius"),
                                        "upper_threshold_critical": t.get(
                                            "UpperThresholdCritical"),
                                        "status": t.get("Status", {}).get(
                                            "Health", ""),
                                    })
                                telemetry["temperatures"] = temps

                    if "power" in metrics:
                        url = f"{base_url}/redfish/v1/Chassis/1/Power"
                        async with session.get(url, ssl=ssl_context,
                                               timeout=aiohttp.ClientTimeout(
                                                   total=15)) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                telemetry["power"] = {
                                    "power_consumed_watts": data.get(
                                        "PowerControl", [{}])[0].get(
                                        "PowerConsumedWatts"),
                                    "power_limit_watts": data.get(
                                        "PowerControl", [{}])[0].get(
                                        "PowerLimit", {}).get("LimitInWatts"),
                                }

                    if "fan_speed" in metrics:
                        url = f"{base_url}/redfish/v1/Chassis/1/Thermal"
                        async with session.get(url, ssl=ssl_context,
                                               timeout=aiohttp.ClientTimeout(
                                                   total=15)) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                fans = []
                                for f in data.get("Fans", []):
                                    fans.append({
                                        "name": f.get("Name", ""),
                                        "reading_rpm": f.get("Reading"),
                                        "status": f.get("Status", {}).get(
                                            "Health", ""),
                                    })
                                telemetry["fans"] = fans

                    if "gpu_errors" in metrics or "ecc_errors" in metrics:
                        url = f"{base_url}/redfish/v1/Systems/1"
                        async with session.get(url, ssl=ssl_context,
                                               timeout=aiohttp.ClientTimeout(
                                                   total=15)) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                oem = data.get("Oem", {}).get("Nvidia", {})
                                if "gpu_errors" in metrics:
                                    telemetry["gpu_errors"] = oem.get(
                                        "GpuErrors", {})
                                if "ecc_errors" in metrics:
                                    telemetry["ecc_errors"] = oem.get(
                                        "EccErrors", {})

                    await queue.put({"dgx_telemetry": telemetry})

            except Exception as exc:
                await queue.put({
                    "dgx_telemetry": {
                        "host": host,
                        "error": str(exc),
                        "timestamp": datetime.now(
                            timezone.utc).isoformat(),
                    },
                })

        await asyncio.sleep(interval)


if __name__ == "__main__":
    import os

    class MockQueue:
        async def put(self, event):
            sanitized = {k: v for k, v in event.items() if k != "raw"}
            print(json.dumps(sanitized, indent=2))

    asyncio.run(main(MockQueue(), {
        "hosts": [os.environ.get("DGX_HOST", "localhost")],
        "username": os.environ.get("DGX_USER", "admin"),
        "password": os.environ.get("DGX_PASSWORD", "changeme"),
        "interval": 60,
    }))
