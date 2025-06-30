import re

def extract_session_id(session_str: str):
    

    match = re.search(r"/sessions(.*?)contexts/", session_str)
    if match:
        extracted_string = match.group(1)
        return extracted_string
    else:
         ""

def get_str_from_item_dict(item_dict: dict):
    return ", ".join([f"{int(value)} {key}" for key, value in item_dict.items()])
