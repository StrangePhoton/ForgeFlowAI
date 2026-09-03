Param(
    [switch]$Fix
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if ($Fix) {
    ruff check --fix forgeflow apps tests
    ruff format forgeflow apps tests
} else {
    ruff check forgeflow apps tests
    ruff format --check forgeflow apps tests
}

mypy forgeflow apps
pytest -q
