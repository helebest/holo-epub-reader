from __future__ import annotations

from pathlib import Path

import cli
from doctor import DoctorResult
from exit_codes import EXIT_DOCTOR_ERROR, EXIT_ERROR, EXIT_OK


def _doctor_ok() -> DoctorResult:
    return DoctorResult(
        ok=True,
        python_path=Path("/home/test/.openclaw/.venv/bin/python3"),
        python_version="3.11.7",
        errors=[],
    )


def _doctor_fail() -> DoctorResult:
    return DoctorResult(
        ok=False,
        python_path=Path("/home/test/.openclaw/.venv/bin/python3"),
        python_version=None,
        errors=["Required Python interpreter not found"],
    )


def test_cli_doctor_success(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "_run_doctor_check", _doctor_ok)

    code = cli.run(["doctor"])

    assert code == EXIT_OK
    captured = capsys.readouterr()
    assert "Doctor OK" in captured.out


def test_cli_doctor_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "_run_doctor_check", _doctor_fail)

    code = cli.run(["doctor"])

    assert code == EXIT_DOCTOR_ERROR
    captured = capsys.readouterr()
    assert "ERROR:" in captured.err


def test_cli_parse_blocks_when_doctor_fails(monkeypatch) -> None:
    called = {"parse": False}

    def fake_parse(*_args, **_kwargs):
        called["parse"] = True
        return {}

    monkeypatch.setattr(cli, "_run_doctor_check", _doctor_fail)
    monkeypatch.setattr(cli, "parse_epub", fake_parse)

    code = cli.run(["parse", "book.epub", "--out", "out"])

    assert code == EXIT_DOCTOR_ERROR
    assert called["parse"] is False


def test_cli_validate_blocks_when_doctor_fails(monkeypatch) -> None:
    called = {"validate": False}

    def fake_validate(*_args, **_kwargs):
        called["validate"] = True
        return True, []

    monkeypatch.setattr(cli, "_run_doctor_check", _doctor_fail)
    monkeypatch.setattr(cli, "validate_output", fake_validate)

    code = cli.run(["validate", "out"])

    assert code == EXIT_DOCTOR_ERROR
    assert called["validate"] is False


def test_cli_parse_success(monkeypatch) -> None:
    called = {"parse": False}

    def fake_parse(epub, out, **kwargs):
        called["parse"] = True
        assert str(epub) == "book.epub"
        assert str(out) == "out"
        assert kwargs["include_images"] is True
        assert kwargs["strip_nav"] is True
        assert kwargs["max_chunk_chars"] == 1200
        return {"blocks": 1}

    monkeypatch.setattr(cli, "_run_doctor_check", _doctor_ok)
    monkeypatch.setattr(cli, "parse_epub", fake_parse)

    code = cli.run(["parse", "book.epub", "--out", "out", "--quiet"])

    assert code == EXIT_OK
    assert called["parse"] is True


def test_cli_parse_runtime_error(monkeypatch, capsys) -> None:
    def fake_parse(*_args, **_kwargs):
        raise RuntimeError("bad parse")

    monkeypatch.setattr(cli, "_run_doctor_check", _doctor_ok)
    monkeypatch.setattr(cli, "parse_epub", fake_parse)

    code = cli.run(["parse", "book.epub", "--out", "out"])

    assert code == EXIT_ERROR
    captured = capsys.readouterr()
    assert "bad parse" in captured.err


def test_cli_validate_success(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "_run_doctor_check", _doctor_ok)
    monkeypatch.setattr(cli, "validate_output", lambda _out: (True, []))

    code = cli.run(["validate", "out"])

    assert code == EXIT_OK
    captured = capsys.readouterr()
    assert "Validation OK" in captured.out


def test_cli_validate_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "_run_doctor_check", _doctor_ok)
    monkeypatch.setattr(cli, "validate_output", lambda _out: (False, ["problem"]))

    code = cli.run(["validate", "out"])

    assert code == EXIT_ERROR
    captured = capsys.readouterr()
    assert "ERROR: problem" in captured.out
