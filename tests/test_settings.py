"""Test that settings come from the environment, with .env values as defaults."""

import importlib
import os
import subprocess

from fastapi.testclient import TestClient

import main
import service.generate_svg
import service.utils.settings as settings

client = TestClient(main.app)

KEY = "SRS_TEST_SETTING"


def reload_settings_from_dotenv(monkeypatch, tmp_path, content):
    (tmp_path / ".env").write_text(content)
    monkeypatch.chdir(tmp_path)
    importlib.reload(settings)


def test_dotenv_file_is_used_as_default(monkeypatch, tmp_path):
    # GIVEN a setting only present in .env
    monkeypatch.delenv(KEY, raising=False)

    # WHEN loading settings
    reload_settings_from_dotenv(monkeypatch, tmp_path, f"{KEY}=from_file\n")

    # THEN the .env value is used
    assert settings.get_setting(KEY) == "from_file"
    monkeypatch.delenv(KEY)


def test_environment_overrides_dotenv_file(monkeypatch, tmp_path):
    # GIVEN a setting both in the environment and in .env
    monkeypatch.setenv(KEY, "from_env")

    # WHEN loading settings
    reload_settings_from_dotenv(monkeypatch, tmp_path, f"{KEY}=from_file\n")

    # THEN the environment wins
    assert settings.get_setting(KEY) == "from_env"


def test_trgt_without_catalog_uses_trgt_catalog(monkeypatch, tmp_path):
    # GIVEN separate default catalogs for REViewer and trgt, and a request without catalog
    monkeypatch.setenv("REV_CATALOG_PATH", "/defaults/reviewer_catalog.json")
    monkeypatch.setenv("TRGT_CATALOG_PATH", "/defaults/trgt_repeats.bed")
    monkeypatch.setenv("TRGT_PATH", "trgt")
    inputs = {}
    for key in ["reads", "reads_index", "vcf"]:
        (tmp_path / key).write_text("data")
        inputs[key] = str(tmp_path / key)

    commands = []

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        with open(cmd[cmd.index("--image") + 1], "w") as svg:
            svg.write("<svg/>")
        return subprocess.CompletedProcess(cmd, 0, stdout=b"")

    monkeypatch.setattr(service.generate_svg.subprocess, "run", fake_run)

    # WHEN requesting a trgt plot
    res = client.post("/trgt", json={**inputs, "locus": "TCF4"})

    # THEN trgt gets the trgt catalog, not the REViewer one
    assert res.status_code == 200
    cmd = commands[0]
    assert cmd[cmd.index("--repeats") + 1] == "/defaults/trgt_repeats.bed"
    assert os.path.isfile(inputs["reads"])
