def serialize_token(token: dict) -> dict:
    # Soportar size como tuple/list O como size_x/size_y separados
    if "size" in token:
        width = token["size"][0]
        height = token["size"][1]
    else:
        width = token.get("size_x", 1)
        height = token.get("size_y", 1)

    # Soportar asset_url O texture
    asset = token.get("asset") or token.get("asset_url") or token.get("texture") or ""

    return {
        "id":     token["id"],
        "x":      token["x"],
        "y":      token["y"],
        "width":  width,
        "height": height,
        "asset":  asset,
        "label":  token.get("label", ""),
        "hp":     token.get("hp", 0),
        "max_hp": token.get("max_hp", 0),
        "ac":     token.get("ac", 10),
    }