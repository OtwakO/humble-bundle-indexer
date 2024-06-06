# -*- coding: utf-8 -*-
import calendar
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil.rrule import MONTHLY, rrule
from loguru import logger

from render_template import render

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

START_YEAR = 2019
START_MONTH = 12
BASE_URL = "https://www.humblebundle.com/membership"

# HEADERS = {
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76",
# }


def get_all_months():
    start = datetime(START_YEAR, START_MONTH, 1)
    current_year = datetime.now().year
    current_month = datetime.now().month
    end = datetime(current_year, current_month, 1)
    all_months = [
        [each.month, str(each.year)]
        for each in rrule(MONTHLY, dtstart=start, until=end)
    ]
    # Convert month number to english
    for month in all_months:
        month[0] = calendar.month_name[month[0]]
    return all_months[::-1]


def get_html(url):
    response = requests.get(url)
    return response.text


def main():
    global all_months
    urls = []
    soups = []
    all_months = get_all_months()
    for month in all_months:
        suffix = f"{month[0]}-{month[-1]}"
        urls.append(f"{BASE_URL}/{suffix}")
    # urls = urls[::-1]
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_html, url) for url in urls]
        all_htmls = [future.result() for future in futures]

    for page in all_htmls:
        soups.append(BeautifulSoup(page, "html.parser"))

    all_games = {"Games": []}
    for index, soup in enumerate(soups):
        try:
            result = soup.select_one("script#webpack-monthly-product-data").text.strip()
        except AttributeError:
            urls.pop(index)
            logger.error(f"Skipping {' '.join(all_months[index])}.")
            all_months.pop(index)
            continue
        if not result:
            urls.pop(index)
            logger.error(f"Skipping {' '.join(all_months[index])}.")
            all_months.pop(index)
            continue
        result_json = json.loads(result)

        if result := find_key(result_json, "game_data"):
            all_games["Games"].append(result["game_data"])
        elif result := find_key(result_json, "content_choices"):
            all_games["Games"].append(result["content_choices"])

        # Save to result.json
        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(all_games, f, indent=2)

        # with open("debug.json", "w", encoding="utf-8") as f:
        #     json.dump(result_json, f, indent=2)

    rendering(urls)


def rendering(urls):
    with open("result.json", "r", encoding="utf-8") as f:
        data = json.load(f)["Games"]
    games = []
    for index, page in enumerate(data):
        page_game = []
        for game, game_info in page.items():
            page_game.append(
                {
                    "title": game_info["title"],
                    "cover": game_info["image"],
                    "link": urls[index],
                    "rating": str(
                        float(game_info["user_rating"].get("steam_percent|decimal", 0))
                        * 100
                    ),
                    "genre": ", ".join(game_info["genres"]),
                    "description": get_description(game_info["description"]),
                }
            )
        games.append(page_game)

    render(games, all_months)


# Recursively find specific key without knowing upper nests
def recursive_logic(dct):
    for key, value in dct.items():
        if isinstance(value, dict):
            yield from (f"{key}||||{sub}" for sub in recursive_logic(value))
        else:
            yield key


def find_key(dct, key_to_find):
    result = dct
    for path in recursive_logic(dct):
        formatted_path = path.split("||||")
        if key_to_find in formatted_path:
            end = formatted_path.index(key_to_find)
            correct_path = [*formatted_path]
    try:
        path_list = correct_path[:end]
        for path in path_list:
            result = result[path]
        return result
    except UnboundLocalError:
        return None


def truncate_description(content, length=50, suffix="..."):
    list_of_words = content.split(" ")
    list_of_words = [word for word in list_of_words if word != ""]
    if len(list_of_words) <= length:
        return content
    else:
        return " ".join(list_of_words[: length + 1]) + suffix


def get_description(content):
    cleaned_text = truncate_description(
        BeautifulSoup(content, "html.parser").text.replace("\n", "")
    )
    cleaned_text = cleaned_text.replace(" . ", ". ").replace(" , ", ", ")
    return cleaned_text


if __name__ == "__main__":
    main()
