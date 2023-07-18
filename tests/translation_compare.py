import json
import os

# Requires running cmd: "pip install flatten_json"
from flatten_json import flatten

from custom_components.mydolphin_plus import DOMAIN

SUPPORTED_LANGUAGES = ["en", "it"]


def _get_json_file(path):
    full_path = os.path.join(
        os.path.dirname(__file__),
        f"..\\custom_components\\{DOMAIN}\\{path}"
    )

    with open(full_path, encoding="utf-8") as json_file:
        json_str = json_file.read()
        content = json.loads(json_str)

        return content


def _get_gaps(lang_name: str):
    strings_json = _get_json_file("strings.json")
    lang_json = _get_json_file(f"translations\\{lang_name}.json")

    strings_keys = flatten(strings_json, separator=".")
    lang_keys = flatten(lang_json, separator=".")

    added_gaps = [key for key in strings_keys if key not in lang_keys]
    removed_gaps = [key for key in lang_keys if key not in strings_keys]

    gaps = {
        "added": added_gaps,
        "removed": removed_gaps
    }

    return gaps


def _compare():
    for lang_name in SUPPORTED_LANGUAGES:
        gaps = _get_gaps(lang_name)
        added_keys = gaps.get("added")
        removed_keys = gaps.get("removed")

        if len(added_keys) + len(removed_keys) > 0:
            print(f"Translations for '{lang_name}' is not up to date.")

            if len(added_keys) > 0:
                print(f"New keys:")
                for key in added_keys:
                    print(f" - {key}")

            if len(removed_keys) > 0:
                print(f"Removed keys:")
                for key in removed_keys:
                    print(f" - {key}")


_compare()