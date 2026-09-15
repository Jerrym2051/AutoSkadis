# Copyright (c) 2026 Zerui Ma
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Full license: see LICENSE in the repository root.

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.bins import delete_bin, get_bin, load_bins, register_bin, set_retrieved
from app.config import FAKE_MODE
from app.magnets import cleanup_magnets, magnets_off, magnets_on, release_pulse, setup_magnets
from app.moonraker import check_moonraker, grip_close, grip_open, home_all, move_to_delivery, move_to_pickup_z, move_to_safe_z, move_xy, move_z, query_position
from app.state import state

app = FastAPI(title="AutoSkadis", version="0.1.0")


class BinCreateRequest(BaseModel):
    name: str
    x: int
    y: int
    tag_id: int = 1


@app.get("/")
def read_root() -> dict:
    return {"message": "AutoSkadis API is running", "fake_mode": FAKE_MODE}


@app.get("/bins")
def list_bins() -> dict:
    return {"bins": load_bins()}


@app.get("/status")
def get_status() -> dict:
    return state.to_dict()


@app.post("/retrieve/{bin_name}")
def retrieve_bin(bin_name: str) -> dict:
    if state.status == "busy":
        raise HTTPException(status_code=409, detail="System is busy")

    bin_data = get_bin(bin_name)
    if not bin_data:
        raise HTTPException(status_code=404, detail=f"Bin '{bin_name}' was not found")

    state.set_busy(f"retrieving {bin_name}")
    state.log(f"Starting retrieve for {bin_name}")

    try:
        setup_magnets()
        if not check_moonraker():
            raise RuntimeError("Moonraker is not reachable")
        home_all()
        move_to_safe_z()
        move_xy(float(bin_data["x"]), float(bin_data["y"]))
        move_to_pickup_z()
        grip_close()
        magnets_on()
        release_pulse()
        move_to_safe_z()
        move_to_delivery()
        grip_open()
        magnets_off()
        set_retrieved(bin_name, True)
        state.retrieved_bins.append(bin_name)
        state.set_idle("retrieval complete")
        state.log(f"Retrieved {bin_name}")
        return {"message": f"Retrieved {bin_name}", "bin": bin_data}
    except Exception as exc:  # pragma: no cover - simple safety path
        state.set_error(str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/return/{bin_name}")
def return_bin(bin_name: str) -> dict:
    if state.status == "busy":
        raise HTTPException(status_code=409, detail="System is busy")

    bin_data = get_bin(bin_name)
    if not bin_data:
        raise HTTPException(status_code=404, detail=f"Bin '{bin_name}' was not found")

    state.set_busy(f"returning {bin_name}")
    state.log(f"Starting return for {bin_name}")

    try:
        setup_magnets()
        if not check_moonraker():
            raise RuntimeError("Moonraker is not reachable")
        home_all()
        move_to_safe_z()
        move_xy(float(bin_data["x"]), float(bin_data["y"]))
        move_to_pickup_z()
        magnets_on()
        grip_open()
        move_to_safe_z()
        move_to_delivery()
        release_pulse()
        magnets_off()
        set_retrieved(bin_name, False)
        state.retrieved_bins = [item for item in state.retrieved_bins if item != bin_name]
        state.set_idle("return complete")
        state.log(f"Returned {bin_name}")
        return {"message": f"Returned {bin_name}", "bin": bin_data}
    except Exception as exc:  # pragma: no cover - simple safety path
        state.set_error(str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/register_bin")
def register_new_bin(request: BinCreateRequest) -> dict:
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Bin name cannot be empty")
    entry = register_bin(request.name, request.x, request.y, request.tag_id)
    return {"message": "Bin registered", "bin": entry}


@app.delete("/bin/{bin_name}")
def delete_bin_endpoint(bin_name: str) -> dict:
    delete_bin(bin_name)
    return {"message": f"Deleted {bin_name}"}


@app.post("/home")
def home_robot() -> dict:
    if state.status == "busy":
        raise HTTPException(status_code=409, detail="System is busy")
    state.set_busy("homing")
    try:
        home_all()
        state.homed = True
        state.set_idle("homed")
        return {"message": "Homed successfully"}
    except Exception as exc:
        state.set_error(str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/magnets/on")
def magnets_on_endpoint() -> dict:
    setup_magnets()
    magnets_on()
    return {"message": "Magnets enabled"}


@app.post("/magnets/off")
def magnets_off_endpoint() -> dict:
    magnets_off()
    return {"message": "Magnets disabled"}


@app.post("/magnets/release")
def magnets_release_endpoint() -> dict:
    release_pulse()
    return {"message": "Release pulse sent"}


@app.on_event("shutdown")
def shutdown_event() -> None:
    cleanup_magnets()
