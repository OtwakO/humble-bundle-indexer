# -*- coding: utf-8 -*-
import os, sys, time, json
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from pprint import pprint
from dataclasses import dataclass, asdict

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

env = Environment(loader=FileSystemLoader("templates/"))

template = env.get_template("gallery.html")


def render(content, all_months):
    output_path = f"{os.path.dirname(os.path.abspath(sys.argv[0]))}\output"
    # with open("result.json", "r", encoding="utf-8") as f:
    #     data = json.load(f)["Games"]
    logger.success(f"Rendering all games...")

    with open(f"output/HumbleChoices.html", "w", encoding="utf-8") as f:
        f.write(
            template.render(
                games=content,
                current_page="HumbleChoices",
                max_page="HumbleChoices",
                all_months=all_months,
                path=output_path.replace("\\", "\\\\"),
            )
        )

    # for page_num, page_content in enumerate(chunk_data, 1):
    #     with open(f"output/{page_num}.html", "w", encoding="utf-8") as f:
    #         f.write(
    #             template.render(
    #                 JavDB=page_content,
    #                 current_page=page_num,
    #                 path=output_path.replace("\\", "\\\\"),
    #                 max_page=len(chunk_data),
    #             )
    #         )
    #     logger.success(f"Rendered {page_num}.html ")

    logger.success(f"Page rendering complete!")


# if __name__ == "__main__":
#     render()
