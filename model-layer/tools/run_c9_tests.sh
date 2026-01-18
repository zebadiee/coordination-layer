#!/usr/bin/env bash
set -euo pipefail

# Run C9 unit tests
pytest -q tests/unit/test_execution_plan.py
