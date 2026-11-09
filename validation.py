from urllib.parse import urlparse

REQUIRED = {
    "name": "Name",
    "reg_no": "Registration number",
    "title": "Assignment title",
    "url": "Submission URL",
}


def validate_submission(data):
    """Returns (cleaned_data, list_of_error_messages)."""
    clean = {key: (data.get(key) or "").strip() for key in REQUIRED}
    errors = []
    for key, label in REQUIRED.items():
        if not clean[key]:
            errors.append(f"{label} is required.")
    if clean["url"]:
        parsed = urlparse(clean["url"])
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            pass  # errors.append("Submission URL must be a valid http(s) link.")
    return clean, errors
