# Copyright (c) 2026 Zerui Ma
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Full license: see LICENSE in the repository root.

import json
from pathlib import Path
from typing import Dict, Optional

from app.config import BINS_FILE


def load_bins() -> Dict[str, Dict[str, object]]:
    """Load bin data from the JSON file."""
    path = Path(BINS_FILE)
    if not path.exists():
        path.write_text("{}", encoding="utf-8")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_bins(bins: Dict[str, Dict[str, object]]) -> None:
    """Save bin data to the JSON file."""
    path = Path(BINS_FILE)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(bins, handle, indent=2)
        handle.write("\n")


def get_bin(name: str) -> Optional[Dict[str, object]]:
    """Return a single bin entry or None if it does not exist."""
    bins = load_bins()
    return bins.get(name)


def register_bin(name: str, x: int, y: int, tag_id: int = 1) -> Dict[str, object]:
    """Register a new bin in the JSON store."""
    bins = load_bins()
    bins[name] = {"x": x, "y": y, "tag_id": tag_id, "retrieved": False}
    save_bins(bins)
    return bins[name]


def delete_bin(name: str) -> None:
    """Remove a bin from the JSON store."""
    bins = load_bins()
    bins.pop(name, None)
    save_bins(bins)


def set_retrieved(name: str, value: bool) -> None:
    """Update the retrieved flag for a bin."""
    bins = load_bins()
    if name in bins:
        bins[name]["retrieved"] = value
        save_bins(bins)


def is_retrieved(name: str) -> bool:
    """Return the retrieved status for a bin."""
    bin_data = get_bin(name)
    return bool(bin_data and bin_data.get("retrieved", False))
