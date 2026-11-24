# Task runner for kochen-specker-extremal-lab (Build Standard v1.1.0)
set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

build:
    bash scripts/dev.sh build

test:
    bash scripts/dev.sh test

lint:
    python3 -m ruff check src/ scripts/ tests/ || true

sanitizers:
    bash scripts/dev.sh sanitizers

verify-lean:
    bash scripts/dev.sh verify-lean

reproduce:
    bash scripts/dev.sh reproduce

audit:
    bash scripts/audit-repo.sh .
