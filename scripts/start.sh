#!/usr/bin/env bash
# Copyright (c) 2026 Zerui Ma
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Full license: see LICENSE in the repository root.
set -euo pipefail
cd "$(dirname "$0")/.."
uvicorn app.main:app --reload
