"""Download the bundled game assets for GeniusLib from the GitHub Release.

The game-data bundle under ``geniuslib/static/assets`` (~413MB) is deliberately
excluded from the source distribution and the PyPI wheel. It ships as the
``geniuslib-assets-<version>.tar.gz`` asset attached to each GitHub Release.
Run this script from the repository root to fetch and extract it locally.
"""

import argparse
import asyncio
import io
import logging
import tarfile
from pathlib import Path

import aiohttp

LOG = logging.getLogger("download_assets")

REPO = "AkumaHalls/GeniusLib"
API_RELEASES = f"https://api.github.com/repos/{REPO}/releases"
DEST_DIR = Path("geniuslib/static/assets")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        default=None,
        help="Version to fetch, e.g. 5.6.0. Defaults to the latest stable release.",
    )
    parser.add_argument(
        "--repo",
        default=REPO,
        help="GitHub repository to fetch the release asset from.",
    )
    parser.add_argument(
        "--dest",
        default=str(DEST_DIR),
        help="Destination directory for the extracted assets.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser.parse_args()


async def resolve_asset_url(session: aiohttp.ClientSession, repo: str, version: str | None) -> str:
    api = f"https://api.github.com/repos/{repo}/releases"
    if version:
        url = f"{api}/tags/v{version}"
    else:
        url = f"{api}/latest"
    async with session.get(url, headers={"Accept": "application/vnd.github+json"}) as resp:
        resp.raise_for_status()
        release = await resp.json()
    expected = f"geniuslib-assets-{version}.tar.gz" if version else None
    for asset in release.get("assets", []):
        name = asset["name"]
        if expected is None and name.startswith("geniuslib-assets-") and name.endswith(".tar.gz"):
            return asset["browser_download_url"]
        if name == expected:
            return asset["browser_download_url"]
    raise RuntimeError(f"No assets tarball found in release {release.get('tag_name')}")


async def download_asset(session: aiohttp.ClientSession, url: str, dest: Path) -> None:
    LOG.info("Downloading %s", url)
    dest.mkdir(parents=True, exist_ok=True)
    async with session.get(url) as resp:
        resp.raise_for_status()
        buf = io.BytesIO()
        while True:
            chunk = await resp.content.read(1 << 16)
            if not chunk:
                break
            buf.write(chunk)
    buf.seek(0)
    with tarfile.open(fileobj=buf, mode="r:gz") as tar:
        for member in tar.getmembers():
            target = (dest / member.name).resolve()
            if not str(target).startswith(str(dest.resolve())):
                raise RuntimeError(f"Unsafe path in archive: {member.name}")
            tar.extract(member, dest)
    LOG.info("Extracted to %s", dest)


async def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    async with aiohttp.ClientSession() as session:
        url = await resolve_asset_url(session, args.repo, args.version)
        await download_asset(session, url, Path(args.dest))


if __name__ == "__main__":
    asyncio.run(main())
