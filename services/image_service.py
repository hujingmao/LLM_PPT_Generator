"""Free image API integration for PPT slides."""

import hashlib
import os
from pathlib import Path
from urllib.parse import quote_plus

import requests

from config.settings import TEMP_IMAGE_DIR
from utils.filename_utils import sanitize_filename


class ImageSearchService:
    """Fetch one landscape image for a slide from Pexels or Unsplash."""

    def __init__(self, cache_dir: Path | None = None, timeout: int = 12):
        self.cache_dir = cache_dir or TEMP_IMAGE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.pexels_api_key = os.getenv("PEXELS_API_KEY")
        self.unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")

    def fetch_slide_image(self, keywords: list[str], fallback_query: str = "") -> Path | None:
        query = self._build_query(keywords, fallback_query)
        if not query:
            return None

        cache_key = hashlib.md5(query.encode("utf-8")).hexdigest()[:12]
        for suffix in (".jpg", ".jpeg", ".png", ".webp"):
            cached = self.cache_dir / f"{sanitize_filename(query)[:32]}_{cache_key}{suffix}"
            if cached.exists():
                return cached

        image_url = self._search_pexels(query) or self._search_unsplash(query)
        if not image_url:
            return None
        return self._download_image(image_url, query, cache_key)

    @staticmethod
    def _build_query(keywords: list[str], fallback_query: str) -> str:
        clean_keywords = [item.strip() for item in keywords if item and item.strip()]
        if clean_keywords:
            return " ".join(clean_keywords[:4])
        return fallback_query.strip()

    def _search_pexels(self, query: str) -> str | None:
        if not self.pexels_api_key:
            return None

        response = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            headers={"Authorization": self.pexels_api_key},
            timeout=self.timeout,
        )
        response.raise_for_status()
        photos = response.json().get("photos") or []
        if not photos:
            return None
        src = photos[0].get("src") or {}
        return src.get("large2x") or src.get("large") or src.get("original")

    def _search_unsplash(self, query: str) -> str | None:
        if not self.unsplash_access_key:
            return None

        response = requests.get(
            "https://api.unsplash.com/search/photos",
            params={
                "query": query,
                "per_page": 1,
                "orientation": "landscape",
                "client_id": self.unsplash_access_key,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        results = response.json().get("results") or []
        if not results:
            return None
        urls = results[0].get("urls") or {}
        return urls.get("regular") or urls.get("full") or urls.get("raw")

    def _download_image(self, image_url: str, query: str, cache_key: str) -> Path | None:
        response = requests.get(image_url, timeout=self.timeout)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        suffix = ".jpg"
        if "png" in content_type:
            suffix = ".png"
        elif "webp" in content_type:
            suffix = ".webp"
        elif "jpeg" in content_type or "jpg" in content_type:
            suffix = ".jpg"
        else:
            parsed_suffix = Path(quote_plus(image_url)).suffix.lower()
            if parsed_suffix in {".jpg", ".jpeg", ".png", ".webp"}:
                suffix = parsed_suffix

        image_path = self.cache_dir / f"{sanitize_filename(query)[:32]}_{cache_key}{suffix}"
        image_path.write_bytes(response.content)
        return image_path
