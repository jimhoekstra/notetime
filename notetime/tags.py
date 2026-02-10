import re


def extract_tags(text: str) -> list[str]:
    tag_pattern = r"@([a-zA-Z0-9_]+)"
    tags: list[str] = re.findall(tag_pattern, text)
    return [tag.lower() for tag in tags]
