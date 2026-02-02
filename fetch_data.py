"""Fetch all anime and manga from AniList, Kitsu, and MangaDex APIs and save to JSON."""

import json
import requests
import time
import re
from typing import List, Dict, Optional
from tqdm import tqdm

OUTPUT_JSON = "anime_manga_all_sources.json"
ANILIST_URL = "https://graphql.anilist.co"
KITSU_BASE = "https://kitsu.io/api/edge"
MANGADEX_BASE = "https://api.mangadex.org"


# -----------------------------
# AniList
# -----------------------------
ANILIST_QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media {
      id
      type
      title { romaji english native }
      description
      genres
      format
      status
      averageScore
      popularity
      tags { name }
      relations { edges { node { id title { romaji } type } relationType } }
      startDate { day month year }
    }
  }
}
"""


def fetch_anilist_page(page: int, per_page: int = 50) -> List[Dict]:
    """Fetch a single page of AniList media."""
    while True:
        try:
            response = requests.post(
                ANILIST_URL,
                json={"query": ANILIST_QUERY, "variables": {"page": page, "perPage": per_page}},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["data"]["Page"]["media"]
        except requests.exceptions.RequestException:
            print(f"Retrying AniList page {page}...")
            time.sleep(5)


def normalize_anilist(media: Dict) -> Dict:
    """Normalize AniList media entry."""
    start_date = media.get("startDate", {})
    return {
        "id": f"ANILIST_{media['id']}",
        "type": media["type"],
        "title_romaji": media["title"].get("romaji"),
        "title_english": media["title"].get("english"),
        "description": media.get("description"),
        "genres": media.get("genres", []),
        "tags": [tag["name"] for tag in media.get("tags", [])],
        "format": media.get("format"),
        "status": media.get("status"),
        "average_score": media.get("averageScore"),
        "popularity": media.get("popularity"),
        "relations": [rel["node"]["id"] for rel in media.get("relations", {}).get("edges", [])],
        "release_year": start_date.get("year"),
        "release_month": start_date.get("month"),
        "release_day": start_date.get("day"),
        "source": "AniList",
    }


# -----------------------------
# Kitsu
# -----------------------------
def fetch_kitsu(endpoint: str) -> List[Dict]:
    """Fetch all media from Kitsu API endpoint."""
    results = []
    url = f"{KITSU_BASE}/{endpoint}?page[limit]=20"
    while url:
        try:
            resp = requests.get(url).json()
            results.extend(resp.get("data", []))
            print(results)
            url = resp.get("links", {}).get("next")
            time.sleep(1)  # avoid rate limits
        except requests.exceptions.RequestException:
            print(f"Retrying Kitsu endpoint {endpoint}...")
            time.sleep(5)
    return results


def normalize_kitsu(media: Dict, media_type: str) -> Dict:
    """Normalize Kitsu media entry."""
    attributes = media.get("attributes", {})
    start_date: Optional[str] = attributes.get("startDate")
    release_year: Optional[int] = None
    if start_date:
        try:
            release_year = int(start_date.split("-")[0])
        except ValueError:
            release_year = None

    return {
        "id": f"KITSU_{media['id']}",
        "type": media_type,
        "title_romaji": attributes.get("canonicalTitle"),
        "title_english": attributes.get("titles", {}).get("en"),
        "description": attributes.get("synopsis"),
        "genres": attributes.get("categories", []),
        "tags": [],
        "format": attributes.get("subtype"),
        "status": attributes.get("status"),
        "release_year": release_year,
        "release_month": None,
        "release_day": None,
        "average_score": attributes.get("averageRating"),
        "popularity": None,
        "relations": [],
        "source": "Kitsu",
    }


# -----------------------------
# MangaDex
# -----------------------------
def fetch_mangadex(limit: int = 100) -> List[Dict]:
    """Fetch all manga from MangaDex API."""
    mangas = []
    offset = 0
    while True:
        try:
            resp = requests.get(f"{MANGADEX_BASE}/manga?limit={limit}&offset={offset}").json()
            data = resp.get("data", [])
            if not data:
                break
            mangas.extend(data)
            offset += limit
            time.sleep(1)  # avoid rate limit
        except requests.exceptions.RequestException:
            print(f"Retrying MangaDex offset {offset}...")
            time.sleep(5)
    return mangas


def normalize_mangadex(media: Dict) -> Dict:
    """Normalize MangaDex media entry."""
    attributes = media.get("attributes", {})
    title_dict = attributes.get("title", {})
    return {
        "id": f"MANGADEX_{media['id']}",
        "type": "MANGA",
        "title_romaji": title_dict.get("en"),
        "title_english": None,
        "description": attributes.get("description", {}).get("en"),
        "genres": [],
        "tags": [],
        "format": attributes.get("publicationDemographic"),
        "status": attributes.get("status"),
        "release_year": None,
        "release_month": None,
        "release_day": None,
        "average_score": None,
        "popularity": None,
        "relations": [],
        "source": "MangaDex",
    }