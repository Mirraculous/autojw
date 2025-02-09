import json
import requests
import time
import os
from pathlib import Path

debug = False
steamapi_search_url = "https://store.steampowered.com/api/storesearch/"

country = "ua"
appnames_filename = "GameList-example.txt"
request_delay = 2
checkpoint_interval = 50
output_dir = "results"

result_filename = f"{output_dir}/results.txt"
multiple_filename = f"{output_dir}/multiple.json"
not_found_filename = f"{output_dir}/not_found.txt"
error_filename = f"{output_dir}/errors.txt"
checkpoint_filename = f"{output_dir}/checkpoint.json"

Path(output_dir).mkdir(parents=True, exist_ok=True)

result_list = []
error_list = []
multiple_list = []
not_found_list = []

with open(appnames_filename, "r", encoding="utf-8") as f:
    appnames_set = set(
        [
            "".join(
                char
                for char in line.strip().lower()
                if char.isalnum() or char.isspace()
            )
            for line in f
        ]
    )
print(f"Apps in text file: {len(appnames_set)}")
print(f"The delay between requests is {request_delay} seconds")
if request_delay:
    print(
        f"Estimated time is "
        f"{len(appnames_set) * request_delay // 60:.0f}m "
        f"{len(appnames_set) * request_delay % 60:.0f}s"
    )
print("Fetching data from Steam, please wait...")


def process_appname(appname, original_appname=None, is_trunc=False):
    """
    Process the application name and search for it in the Steam store.

    Args:
        appname (str): The name of the application to search for.
        original_appname (str, optional): The original name of the application. Defaults to None.
        is_trunc (bool, optional): Whether the application name is truncated. Defaults to False.

    Returns:
        bool: True if the application is found, False otherwise.
    """
    params = {"term": appname, "cc": country}
    try:
        response = requests.get(url=steamapi_search_url, params=params)
        response.raise_for_status()
        result = response.json()
        if result.get("total", 0) == 0:
            split_appname = appname.split()[:-1]
            if len(split_appname) > 0:
                trunc_appname = " ".join(split_appname)
                time.sleep(request_delay)
                if debug:
                    print(f"Truncating {appname} to {trunc_appname}")
                return process_appname(
                    trunc_appname,
                    original_appname=original_appname or appname,
                    is_trunc=True,
                )
            not_found_list.append(
                {"appname": original_appname or appname, "found_as": None}
            )
            return False
        if result["total"] > 1:
            multiple_list.append(
                {
                    "appname": appname,
                    "total": result["total"],
                    "secondary": [
                        {
                            "name": item["name"],
                            "id": item["id"],
                            "initial": item.get("price", {"initial": 0})["initial"],
                        }
                        for item in result["items"][1:]
                    ],
                    "original_appname": original_appname or appname,
                }
            )
        item = result["items"][0]
        result_list.append(
            {
                "name": item["name"],
                "id": item["id"],
                "initial": item.get("price", {"initial": 0})["initial"],
                "original_appname": original_appname or appname,
            }
        )
        if is_trunc:
            not_found_list.append({"appname": original_appname, "found_as": appname})
        return True
    except Exception as e:
        error_list.append(
            {"appname": appname, "url": response.url, "exception": str(e)}
        )
        return False


for i, appname in enumerate(appnames_set):
    if i and checkpoint_interval and (i % checkpoint_interval) == 0:
        print(f"{i} items done, making a checkpoint")
        print(
            f"Successful results: {len(result_list)} "
            f"(Multiple: {len(multiple_list)}) / "
            f"Errors: {len(error_list)} / "
            f"Not found: {len(not_found_list)} "
            f"(Found truncated: {sum(app["found_as"] != None for app in not_found_list)})"
        )
        with open(f"{checkpoint_filename}.tmp", "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "result_list": result_list,
                        "error_list": error_list,
                        "multiple_list": multiple_list,
                        "not_found_list": not_found_list,
                    },
                    indent=4,
                )
            )
        os.replace(f"{checkpoint_filename}.tmp", checkpoint_filename)
    process_appname(appname)
    time.sleep(request_delay)

with open(error_filename, "w", encoding="utf-8") as f:
    if len(error_list) > 0:
        print(f"\nErrors (written to {error_filename}):")
        for err in error_list:
            err_string = (
                f"App Name: {err["appname"]}\n"
                f"Request URL: {err["url"]}\n"
                f"Exception: {err["exception"]}\n\n"
            )
            print(err_string)
            f.write(err_string)

with open(not_found_filename, "w", encoding="utf-8") as f:
    if len(not_found_list) > 0:
        print(f"\nApps not found (written to {not_found_filename}):")
        for app in not_found_list:
            print(
                f"{app["appname"]} "
                f"({f"Found as: {app["found_as"]}" if app["found_as"] else "Not found"})"
            )
            f.write(
                f"{app["appname"]} "
                f"({f"Found as: {app["found_as"]}" if app["found_as"] else "Not found"})\n"
            )

with open(multiple_filename, "w", encoding="utf-8") as f:
    if len(multiple_filename) > 0:
        print(
            "\nMultiple results found for apps "
            f"(JSON written to {multiple_filename}):"
        )
        for app in multiple_list:
            print(f"{app["appname"]}: {app["total"]} results"
                  f"{f" (Original appname: {app["original_appname"]})" if app["original_appname"] else ""}")
        f.write(json.dumps(multiple_list, indent=4))

result_list.sort(key=lambda x: x["initial"], reverse=True)
with open(result_filename, "w", encoding="utf-8") as f:
    print(
        f"\nApps sorted by price in {country.upper()} store "
        f"(written to {result_filename}):"
    )
    for app in result_list:
        print(f"{app["name"]} ({app["id"]}) - {app["initial"]/100:.2f}"
              f"{f" (Original appname: {app["original_appname"]})" if app["original_appname"] else ""}")
        f.write(f"{app["name"]} ({app["id"]}) - {app["initial"]/100:.2f}"
                f"{f" (Original appname: {app["original_appname"]})" if app["original_appname"] else ""}\n")
