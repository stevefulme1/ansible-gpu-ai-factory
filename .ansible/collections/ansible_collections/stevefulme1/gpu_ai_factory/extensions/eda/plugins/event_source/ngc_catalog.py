"""EDA event source plugin for NGC catalog monitoring."""

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
    """Watch NGC catalog for new container image releases.

    Polls the NGC catalog API for new image tags and emits events
    when new versions are detected for watched images.

    Args:
        queue: The EDA event queue.
        args: Configuration arguments:
            - ngc_api_key: NGC API key for authentication
            - images: List of NGC image names to watch
              (e.g., ["nvidia/nemo", "nvidia/tritonserver"])
            - interval: Polling interval in seconds (default: 300)
            - ngc_org: NGC organization (default: nvidia)
    """
    ngc_api_key = args.get("ngc_api_key", "")
    images = args.get("images", [])
    interval = int(args.get("interval", 300))
    ngc_org = args.get("ngc_org", "nvidia")

    headers = {}
    if ngc_api_key:
        headers["Authorization"] = f"Bearer {ngc_api_key}"

    known_tags = {}

    while True:
        for image in images:
            image_name = image.split("/")[-1] if "/" in image else image
            org = image.split("/")[0] if "/" in image else ngc_org
            url = (
                f"https://api.ngc.nvidia.com/v2/org/{org}"
                f"/containers/{image_name}/tags"
            )

            try:
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        if resp.status != 200:
                            continue

                        data = await resp.json()
                        tags = data.get("tags", data.get("results", []))

                        current_tags = set()
                        for tag in tags:
                            tag_name = tag if isinstance(tag, str) else tag.get(
                                "name", tag.get("tag", ""))
                            current_tags.add(tag_name)

                        prev_tags = known_tags.get(image, set())
                        new_tags = current_tags - prev_tags

                        if prev_tags and new_tags:
                            for tag_name in sorted(new_tags):
                                await queue.put({
                                    "ngc_catalog": {
                                        "event_type": "new_image",
                                        "image": f"nvcr.io/{org}/{image_name}",
                                        "tag": tag_name,
                                        "full_image": (
                                            f"nvcr.io/{org}"
                                            f"/{image_name}:{tag_name}"
                                        ),
                                        "timestamp": datetime.now(
                                            timezone.utc).isoformat(),
                                    },
                                })

                        known_tags[image] = current_tags

            except Exception as exc:
                await queue.put({
                    "ngc_catalog": {
                        "event_type": "error",
                        "image": image,
                        "error": str(exc),
                        "timestamp": datetime.now(
                            timezone.utc).isoformat(),
                    },
                })

        await asyncio.sleep(interval)


if __name__ == "__main__":

    class MockQueue:
        async def put(self, event):
            print(json.dumps(event, indent=2))

    asyncio.run(main(MockQueue(), {
        "images": ["nvidia/nemo", "nvidia/tritonserver"],
        "interval": 60,
    }))
