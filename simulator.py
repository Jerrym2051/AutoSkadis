# Copyright (c) 2026 Zerui Ma
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Full license: see LICENSE in the repository root.

import json
import random
import time
from datetime import datetime

bin_pool = ["M3 screws", "M4 screws", "Resistors", "Capacitors", "LEDs", "Diodes", "Jumper wires", "Heat shrink", "Zip ties", "Washers", "Springs", "Fuses"]

retrieved_bins = []

action_log = []

current_status = "Idle"

print("bin_pool:", bin_pool)
print("retrieved_bins:", retrieved_bins)
print("action_log:", action_log)
print("current_status:", current_status)

print("AutoSkadis simulator running. Press Ctrl+C to stop.")

def write_state():
    # Get the 20 most recent entries, reversed (most recent first)
    recent_log = list(reversed(action_log[-20:]))
    state = {
        "status": current_status,
        "retrieved_bins": retrieved_bins,
        "action_log": recent_log
    }
    with open("state.json", "w") as f:
        json.dump(state, f, indent=2)


print("\n--- Simulation started ---\n")

write_state()

try:
    while True:
        # Random wait time between 30 and 60 seconds
        wait_time = random.uniform(30, 60)
        time.sleep(wait_time)
        
        # Weighted action choice based on current retrieved_bins count
        num_retrieved = len(retrieved_bins)
        if num_retrieved <= 2:
            retrieve_prob = 0.8
        elif num_retrieved <= 5:
            retrieve_prob = 0.5
        else:
            retrieve_prob = 0.2
        
        # Check if RETRIEVE is possible
        can_retrieve = len(retrieved_bins) < 8 and len(bin_pool) > len(retrieved_bins)
        # Check if RETURN is possible
        can_return = len(retrieved_bins) > 0
        
        # Determine actual action to take based on weighted probability
        if random.random() < retrieve_prob:
            actual_action = "RETRIEVE"
        else:
            actual_action = "RETURN"
        
        # Handle fallbacks if chosen action is not possible
        if actual_action == "RETRIEVE" and not can_retrieve:
            if can_return:
                actual_action = "RETURN"
            else:
                print(f"[{datetime.now().strftime('%H:%M')}] Cannot retrieve (at capacity or no bins left), nothing to return")
                continue
        elif actual_action == "RETURN" and not can_return:
            if can_retrieve:
                actual_action = "RETRIEVE"
            else:
                print(f"[{datetime.now().strftime('%H:%M')}] Cannot return (empty), cannot retrieve (at capacity or no bins left)")
                continue
        
        if actual_action == "RETRIEVE":
            # RETRIEVE action sequence (FIFO - first available bin)
            available_bins = [b for b in bin_pool if b not in retrieved_bins]
            chosen_bin = available_bins[0]  # Pick first available bin
            
            # Step 1: Moving (3 seconds)
            current_status = "Moving"
            write_state()
            print(f"[{datetime.now().strftime('%H:%M')}] Status: Moving")
            time.sleep(3)
            
            # Step 2: Retrieving (5 seconds)
            current_status = f"Retrieving {chosen_bin}"
            write_state()
            print(f"[{datetime.now().strftime('%H:%M')}] Status: Retrieving {chosen_bin}")
            time.sleep(5)
            
            # Step 3: Complete
            retrieved_bins.append(chosen_bin)
            action_log.append({"time": datetime.now().strftime("%H:%M"), "action": f"Retrieved {chosen_bin}"})
            current_status = "Idle"
            write_state()
            print(f"[{datetime.now().strftime('%H:%M')}] Retrieved: {chosen_bin}")
            
        else:  # actual_action == "RETURN"
            # RETURN action sequence (FIFO - first/oldest retrieved bin)
            chosen_bin = retrieved_bins[0]  # Pick first (oldest) bin
            
            # Step 1: Moving (3 seconds)
            current_status = "Moving"
            write_state()
            print(f"[{datetime.now().strftime('%H:%M')}] Status: Moving")
            time.sleep(3)
            
            # Step 2: Returning (5 seconds)
            current_status = f"Returning {chosen_bin}"
            write_state()
            print(f"[{datetime.now().strftime('%H:%M')}] Status: Returning {chosen_bin}")
            time.sleep(5)
            
            # Step 3: Complete
            retrieved_bins.remove(chosen_bin)
            action_log.append({"time": datetime.now().strftime("%H:%M"), "action": f"Returned {chosen_bin}"})
            current_status = "Idle"
            write_state()
            print(f"[{datetime.now().strftime('%H:%M')}] Returned: {chosen_bin}")
        
        # Print current state
        print(f"\n--- State ---")
        print(f"Retrieved bins ({len(retrieved_bins)}/8): {retrieved_bins}")
        print(f"Action log entries: {len(action_log)}")
        print(f"Status: {current_status}")
        print(f"-------------\n")
except KeyboardInterrupt:
    print("\nSimulator stopped.")
