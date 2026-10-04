"""
Created September 19, 2026

@author montreal91

Loading and validation of static club presentation data.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
from typing import List

_CLUB_INFO_PATH = Path("data/club_info.json")
_CLUB_DESCRIPTIONS_PATH = Path("data/club_descriptions")


@dataclass(frozen=True)
class StaticClubInfo:
    country: str
    city: str
    motto: str
    description: str


def load_club_info_by_id(club_ids: List[str]) -> Dict[str, StaticClubInfo]:
    with _CLUB_INFO_PATH.open(encoding="utf-8-sig") as info_file:
        raw_infos = json.load(info_file)

    infos = {}
    for raw_info in raw_infos:
        club_id = raw_info["club_id"]
        if club_id in infos:
            raise ValueError(f"Duplicate club info for {club_id}.")

        description_path = _CLUB_DESCRIPTIONS_PATH / f"{club_id}.md"
        if not description_path.is_file():
            raise ValueError(f"Missing description for {club_id}.")

        infos[club_id] = StaticClubInfo(
            country=raw_info["country"],
            city=raw_info["city"],
            motto=raw_info["motto"],
            description=description_path.read_text(
                encoding="utf-8-sig"
            ).strip(),
        )

    expected_ids = set(club_ids)
    if set(infos) != expected_ids:
        missing_ids = expected_ids - set(infos)
        unexpected_ids = set(infos) - expected_ids
        raise ValueError(
            "Club info does not match clubs.csv: "
            f"missing={sorted(missing_ids)}, unexpected={sorted(unexpected_ids)}."
        )

    return infos
