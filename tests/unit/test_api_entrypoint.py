"""API container startup sequence."""

from unittest.mock import patch

from forgeflow.api.entrypoint import main, run_migrations


def test_run_migrations_invokes_alembic_upgrade() -> None:
    with patch("forgeflow.api.entrypoint.subprocess.run") as run:
        run_migrations()
        run.assert_called_once()
        command = run.call_args.args[0]
        assert command[-2:] == ["upgrade", "head"]
        assert run.call_args.kwargs["check"] is True


def test_main_migrates_then_starts_uvicorn() -> None:
    with (
        patch("forgeflow.api.entrypoint.run_migrations") as migrate,
        patch("forgeflow.api.entrypoint.uvicorn.run") as run,
    ):
        main()
        migrate.assert_called_once()
        run.assert_called_once()
        assert run.call_args.args[0] == "apps.api.main:app"
        assert run.call_args.kwargs["host"] == "0.0.0.0"
        assert run.call_args.kwargs["port"] == 8000
