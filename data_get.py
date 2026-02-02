
import json
import requests
import time
import re
from typing import List, Dict, Optional
from tqdm import tqdm
import fetch_data as fetch
# -----------------------------
# Main
# -----------------------------
def main() -> None:
    """Fetch all anime/manga from AniList, Kitsu, MangaDex and save to JSON."""
    # all_items: List[Dict] = []

    # # 1️AniList
    # print("FETCHING ANIME AND MANGA")
    # print("ANI LIST")
    # page = 1
    # while True:
    #     media_list = fetch.fetch_anilist_page(page, per_page=100    )
    #     if not media_list:
    #         break
    #     for media in media_list:
    #         all_items.append(fetch.normalize_anilist(media))
    #     print(f"AniList page {page} fetched, total items: {len(all_items)}")
    #     page += 1
    
    # # Save JSON
    # with open(fetch.OUTPUT_JSON_ANILIST, "w", encoding="utf-8") as f:
    #     json.dump(all_items, f, ensure_ascii=False, indent=2)
    
    # print("DONE")

    #### Kitsu 
    
    all_items: List[Dict] = []
    # 2Kitsu Anime
    print("KITSU")
    for media in tqdm(fetch.fetch_kitsu("anime")):
        all_items.append(fetch.normalize_kitsu(media, "ANIME"))

    # 3️Kitsu Manga
    for media in tqdm(fetch.fetch_kitsu("manga")):
        all_items.append(fetch.normalize_kitsu(media, "MANGA"))

    with open(fetch.OUTPUT_JSON_KITSU, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    print("DONE")
    
    all_items: List[Dict] = []
    # 4️MangaDex Manga
    print("MANGADEX")
    for media in tqdm(fetch.fetch_mangadex()):
        all_items.append(fetch.normalize_mangadex(media))

    # Save JSON
    with open(fetch.OUTPUT_JSON_MANGADEX, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    print("DONE")
    
    print(f"Saved All Items")


if __name__ == "__main__":
    main()