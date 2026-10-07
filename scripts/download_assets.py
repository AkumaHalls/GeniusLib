"""Download the bundled game assets for GeniusLib from the GitHub Release.

The game-data bundle under ``geniuslib/static/assets`` (~413MB) is deliberately
excluded from the source distribution and the PyPI wheel. It ships as the
``geniuslib-assets-<version>.tar.gz`` asset attached to each GitHub Release.
Run this script from the repository root to fetch and extract it locally.
"""

import argparse
import asyncio
import hashlib
import io
import logging
import tarfile
from pathlib import Path
from urllib.parse import urlsplit

import aiohttp

LOG = logging.getLogger("download_assets")

REPO = "AkumaHalls/GeniusLib"
API_RELEASES = f"https://api.github.com/repos/{REPO}/releases"
DEST_DIR = Path("geniuslib/static/assets")

# Hosts that may serve the release tarball (``browser_download_url`` plus the
# GitHub content hosts reached through its redirects).
ALLOWED_DOWNLOAD_HOSTS = frozenset(
    {
        "github.com",
        "objects.githubusercontent.com",
        "release-assets.githubusercontent.com",
    }
)

# A malicious or compromised download source could stream forever; the asset
# bundle is ~0.5GB, so 1GB is a generous but bounded ceiling.
MAX_DOWNLOAD_BYTES = 1 << 30


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


def _is_allowed_download_host(host: str | None) -> bool:
    host = (host or "").lower().rstrip(".")
    return host in ALLOWED_DOWNLOAD_HOSTS


async def resolve_asset(session: aiohttp.ClientSession, repo: str, version: str | None) -> tuple[str, str | None]:
    """Return the tarball download URL and its GitHub-published SHA-256 digest, if any."""
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
            return asset["browser_download_url"], asset.get("digest")
        if name == expected:
            return asset["browser_download_url"], asset.get("digest")
    raise RuntimeError(f"No assets tarball found in release {release.get('tag_name')}")


def _extract_safely(tar: tarfile.TarFile, dest: Path) -> None:
    base = dest.resolve()
    for member in tar.getmembers():
        # Only regular files and directories are welcome. Symlinks/hardlinks are
        # rejected outright: a link whose target escapes ``dest`` would make a
        # later extraction write through it, outside the destination.
        if not (member.isfile() or member.isdir()):
            raise RuntimeError(f"Refusing to extract unsupported member {member.name!r}")
        target = (dest / member.name).resolve()
        if not target.is_relative_to(base):
            raise RuntimeError(f"Unsafe path in archive: {member.name}")
        try:
            tar.extract(member, dest, filter="data")
        except TypeError:
            # Python < 3.12 has no data filter; the manual checks above already
            # restricted members to relative files/directories.
            tar.extract(member, dest)


async def download_asset(session: aiohttp.ClientSession, url: str, digest: str | None, dest: Path) -> None:
    LOG.info("Downloading %s", url)
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not _is_allowed_download_host(parsed.hostname):
        raise RuntimeError(f"Refusing to download from untrusted host: {url}")

    dest.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    total = 0
    async with session.get(url) as resp:
        resp.raise_for_status()
        if resp.url is not None and not _is_allowed_download_host(resp.url.host):
            raise RuntimeError(f"Redirected to untrusted host: {resp.url}")
        buf = io.BytesIO()
        while True:
            chunk = await resp.content.read(1 << 16)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD_BYTES:
                raise RuntimeError(f"Download exceeded {MAX_DOWNLOAD_BYTES} bytes; aborting.")
            buf.write(chunk)
            hasher.update(chunk)

    if digest:
        # GitHub exposes the digest as "sha256:<hex>".
        expected = digest.split(":", 1)[1].strip() if ":" in digest else digest
        if hasher.hexdigest().lower() != expected.lower():
            raise RuntimeError(
                f"SHA-256 mismatch: expected {expected}, got {hasher.hexdigest()}. Refusing to extract."
            )
        LOG.info("SHA-256 verified: %s", expected)

    buf.seek(0)
    with tarfile.open(fileobj=buf, mode="r:gz") as tar:
        _extract_safely(tar, dest)
    LOG.info("Extracted %s bytes to %s", total, dest)


async def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    async with aiohttp.ClientSession() as session:
        url, digest = await resolve_asset(session, args.repo, args.version)
        await download_asset(session, url, digest, Path(args.dest))


if __name__ == "__main__":
    asyncio.run(main())
