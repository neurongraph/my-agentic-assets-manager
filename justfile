default:
    @just --list

install:
    uv tool install --reinstall .

setup:
    uv sync
    uv tool install --reinstall .
    maam doctor

sync:
    uv sync

test:
    uv run pytest

test-file FILE:
    uv run pytest {{ FILE }} -v

test-one NAME:
    uv run pytest -k {{ NAME }} -v

doctor:
    uv run maam doctor
