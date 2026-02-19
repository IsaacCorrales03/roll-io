def normalize_token(token: dict) -> dict:
    if "size" in token:
        size = token["size"]
    else:
        size = [
            token.get("size_x", 1),
            token.get("size_y", 1)
        ]

    return {
        **token,
        "size": size
    }
