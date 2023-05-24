import json


def write_to_json(data, json_path):
    with open(json_path, "w") as file:
        json.dump(data, file, ensure_ascii=False)
