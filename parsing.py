from __future__ import annotations
import re
from models import HUB, ParseResult, ParserError


DRONES = re.compile(r"^nb_drones:\s+([1-9]\d*)\s*$")
HUB_PATTERN = re.compile(
    r"^(start_hub|end_hub|hub):\s+(\S+)\s+(-?\d+)\s+(-?\d+)\s*"
    r"(?:\[([^\]]*)\])?\s*$"
)
CONN = re.compile(
    r"^connection:\s+(\S+)\s*(?:\[([^\]]*)\])?\s*$"
)
VALID_ZONES = {"normal", "blocked", "restricted", "priority"}


def fileparse(filename: str) -> ParseResult:
    dr_n: int | None = None
    links_seen: set[tuple[str, str]] = set()
    start_hub = 0
    end_hub = 0
    hub_dic: dict[str, HUB] = {}
    start_obj: HUB | None = None
    end_obj: HUB | None = None

    try:
        with open(filename, 'r') as f:
            for i, lines in enumerate(f, 1):
                line = lines.strip()
                if not line or line.startswith("#"):
                    continue

                dr = DRONES.match(line)
                if dr:
                    if dr_n is not None:
                        raise ParserError(i, "nb_drones defined twice")
                    dr_n = int(dr.group(1))
                    continue

                hu = HUB_PATTERN.match(line)
                if hu:
                    h_type = hu.group(1)
                    name = hu.group(2)
                    x = int(hu.group(3))
                    y = int(hu.group(4))
                    metadata = hu.group(5)
                    if '-' in name:
                        raise ParserError(i, "no '-' in name")

                    meta = parse_metadata(metadata, i)
                    if name in hub_dic:
                        raise ParserError(
                            i, f"duplicate zone name '{name}'"
                        )
                    ob_hub = HUB(name, x, y, h_type, meta)
                    ob_hub.line_num = i

                    if h_type == "start_hub":
                        start_hub += 1
                        start_obj = ob_hub

                    if h_type == "end_hub":
                        end_hub += 1
                        end_obj = ob_hub

                    if start_hub > 1:
                        raise ParserError(
                            i, "start_hub must appear only once"
                        )

                    if end_hub > 1:
                        raise ParserError(
                            i, "end_hub must appear only once"
                        )

                    hub_dic[name] = ob_hub
                    continue

                cn = CONN.match(line)
                if cn:
                    con = cn.group(1)
                    meta_raw = cn.group(2)
                    z1, z2 = con.split('-', 1)

                    if z1 not in hub_dic or z2 not in hub_dic:
                        raise ParserError(
                            i, f"zone '{z1}' or '{z2}' not defined"
                        )
                    pair_tuple = tuple(sorted([z1, z2]))
                    pair: tuple[str, str] = pair_tuple  # type: ignore
                    if pair in links_seen:
                        raise ParserError(i, "duplicate conn")

                    conn_meta = parse_metadata(meta_raw, i)
                    cap = conn_meta.get('max_link_capacity', 1)
                    if not isinstance(cap, int):
                        cap = int(cap)

                    hub_dic[z1].links_capacity[z2] = cap
                    hub_dic[z2].links_capacity[z1] = cap
                    hub_dic[z1].links.append(z2)
                    hub_dic[z2].links.append(z1)
                    links_seen.add(pair)
                    continue
                raise ParserError(i, "unrecognized line syntax")

            if dr_n is None:
                raise ParserError(0, "nb_drones not defined")
            if start_hub != 1 or start_obj is None:
                raise ParserError(0, "no start_hub defined")
            if end_hub != 1 or end_obj is None:
                raise ParserError(0, "no end_hub defined")

            if len(start_obj.links) == 0:
                raise ParserError(
                    start_obj.line_num, "start hub has no connections"
                )
            if len(end_obj.links) == 0:
                raise ParserError(
                    end_obj.line_num, "end hub has no connections"
                )

            if end_obj.zone_type == 'blocked':
                raise ParserError(end_obj.line_num, "no path found")

            for name, h in hub_dic.items():
                if len(h.links) == 0 and h.zone_type != 'blocked':
                    raise ParserError(
                        h.line_num, f"zone '{name}' has no connections"
                    )

        return ParseResult(dr_n, hub_dic, start_obj, end_obj)
    except FileNotFoundError:
        raise ParserError(0, f"file '{filename}' not found")


def parse_metadata(
    meta: str | None, line_num: int
) -> dict[str, str | int]:

    if meta is None:
        return {}

    result = meta.strip().split()
    meta_s: dict[str, str | int] = {}

    for token in result:
        if '=' not in token:
            raise ParserError(line_num, "invalid token")
        key, value = token.split('=', 1)
        if key in meta_s:
            raise ParserError(line_num, f"duplicate key '{key}'")
        if key == 'zone':
            if value not in VALID_ZONES:
                raise ParserError(
                    line_num, f"invalid zone type '{value}'"
                )
            meta_s[key] = value
        elif key in ('max_drones', 'max_link_capacity'):
            try:
                x = int(value)
            except ValueError:
                raise ParserError(line_num, "failed casting")
            if x < 1:
                raise ParserError(line_num, "capacity must be >= 1")

            meta_s[key] = x

        elif key == 'color':
            meta_s[key] = value
        else:
            raise ParserError(line_num, "unknown key")

    return meta_s
