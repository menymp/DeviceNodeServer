import json

# Helper parsers and validators
def parse_int(s, name, minimum=None, maximum=None, required=False):
    if s is None:
        if required:
            raise ValueError(f"missing {name}")
        return None
    try:
        v = int(s)
    except Exception:
        raise ValueError(f"invalid integer for {name}: {s!r}")
    if minimum is not None and v < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    if maximum is not None and v > maximum:
        raise ValueError(f"{name} must be <= {maximum}")
    return v

def parse_bool(s, default=False):
    if s is None:
        return default
    s2 = s.strip().lower()
    if s2 in ("1", "true", "yes", "on"):
        return True
    if s2 in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"invalid boolean value: {s!r}")

def parse_id_list(request, name="idList"):
    # support repeated keys (?idList=1&idList=2) or comma-separated (?idList=1,2,3)
    vals = request.query.getall(name, [])
    if not vals:
        return []
    if len(vals) == 1 and "," in vals[0]:
        parts = [p.strip() for p in vals[0].split(",") if p.strip() != ""]
    else:
        parts = vals
    ids = []
    for p in parts:
        try:
            ids.append(int(p))
        except Exception:
            raise ValueError(f"invalid integer in {name}: {p!r}")
    return ids