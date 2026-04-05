from __future__ import annotations

from pathlib import Path
import subprocess

from holo_epub_reader.doctor import DoctorResult, run_doctor


def _ok_runner(_command):
    return subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='{"major": 3, "minor": 11, "micro": 6}',
        stderr="",
    )


def test_doctor_success(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    python_path = home / ".openclaw" / ".venv" / "bin" / "python3"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("#!/bin/sh\n", encoding="utf-8")

    monkeypatch.setattr("os.access", lambda _path, _mode: True)

    result = run_doctor(env={"HOME": str(home)}, run_command=_ok_runner)

    assert result == DoctorResult(
        ok=True,
        python_path=python_path,
        python_version="3.11.6",
        errors=[],
    )


def test_doctor_success_with_epub_reader_python(tmp_path: Path, monkeypatch) -> None:
    """EPUB_READER_PYTHON env var is used when set."""
    custom_python = tmp_path / "custom" / "python3"
    custom_python.parent.mkdir(parents=True)
    custom_python.write_text("#!/bin/sh\n", encoding="utf-8")

    monkeypatch.setattr("os.access", lambda _path, _mode: True)

    result = run_doctor(
        env={"EPUB_READER_PYTHON": str(custom_python)},
        run_command=_ok_runner,
    )

    assert result.ok
    assert result.python_path == custom_python
    assert result.python_version == "3.11.6"


def test_doctor_env_var_takes_priority(tmp_path: Path, monkeypatch) -> None:
    """EPUB_READER_PYTHON takes priority over OpenClaw path."""
    custom_python = tmp_path / "custom" / "python3"
    custom_python.parent.mkdir(parents=True)
    custom_python.write_text("#!/bin/sh\n", encoding="utf-8")

    home = tmp_path / "home"
    openclaw_python = home / ".openclaw" / ".venv" / "bin" / "python3"
    openclaw_python.parent.mkdir(parents=True)
    openclaw_python.write_text("#!/bin/sh\n", encoding="utf-8")

    monkeypatch.setattr("os.access", lambda _path, _mode: True)

    result = run_doctor(
        env={"EPUB_READER_PYTHON": str(custom_python), "HOME": str(home)},
        run_command=_ok_runner,
    )

    assert result.ok
    assert result.python_path == custom_python


def test_doctor_fails_no_candidates() -> None:
    """No HOME and no EPUB_READER_PYTHON means no candidates."""
    result = run_doctor(env={})
    assert not result.ok
    assert result.python_path is None
    assert "No Python interpreter found" in result.errors[0]


def test_doctor_fails_when_python_missing(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir(parents=True)

    result = run_doctor(env={"HOME": str(home)})

    assert not result.ok
    assert "not found" in result.errors[0]


def test_doctor_fails_when_python_not_executable(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    python_path = home / ".openclaw" / ".venv" / "bin" / "python3"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("#!/bin/sh\n", encoding="utf-8")

    monkeypatch.setattr("os.access", lambda _path, _mode: False)

    result = run_doctor(env={"HOME": str(home)})

    assert not result.ok
    assert "not executable" in result.errors[0]


def test_doctor_fails_when_version_too_low(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    python_path = home / ".openclaw" / ".venv" / "bin" / "python3"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("#!/bin/sh\n", encoding="utf-8")

    def fake_runner(_command):
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"major": 3, "minor": 9, "micro": 18}',
            stderr="",
        )

    monkeypatch.setattr("os.access", lambda _path, _mode: True)

    result = run_doctor(env={"HOME": str(home)}, run_command=fake_runner)

    assert not result.ok
    assert "below minimum 3.10" in result.errors[0]


def test_doctor_fails_when_runner_returns_non_zero(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    python_path = home / ".openclaw" / ".venv" / "bin" / "python3"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("#!/bin/sh\n", encoding="utf-8")

    def fake_runner(_command):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=_command,
            stderr="boom",
        )

    monkeypatch.setattr("os.access", lambda _path, _mode: True)

    result = run_doctor(env={"HOME": str(home)}, run_command=fake_runner)

    assert not result.ok
    assert "non-zero exit code" in result.errors[0]
    assert "boom" in result.errors[0]


def test_doctor_fails_when_payload_is_invalid(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    python_path = home / ".openclaw" / ".venv" / "bin" / "python3"
    python_path.parent.mkdir(parents=True)
    python_path.write_text("#!/bin/sh\n", encoding="utf-8")

    def fake_runner(_command):
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="not-json",
            stderr="",
        )

    monkeypatch.setattr("os.access", lambda _path, _mode: True)

    result = run_doctor(env={"HOME": str(home)}, run_command=fake_runner)

    assert not result.ok
    assert "Unable to parse Python version" in result.errors[0]
