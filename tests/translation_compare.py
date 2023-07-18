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

    gaps = [key for key in strings_keys if key not in lang_keys]

    return gaps


for lang_name in SUPPORTED_LANGUAGES:
    missing_keys = _get_gaps(lang_name)

    if len(missing_keys) > 0:
        print(f"Following keys are missing for {lang_name}:")
        for key in missing_keys:
            print(f" - {key}")
