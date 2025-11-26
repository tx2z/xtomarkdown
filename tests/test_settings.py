"""Tests for the Settings class and configuration persistence."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from xtomarkdown.config.settings import Settings


class TestSettingsDefaults:
    """Test default Settings values."""

    def test_default_output_mode(self):
        """Default output mode should be 'same'."""
        settings = Settings()
        assert settings.output_mode == "same"

    def test_default_output_folder(self):
        """Default output folder should be None."""
        settings = Settings()
        assert settings.output_folder is None

    def test_default_engine_overrides(self):
        """Default engine overrides should be empty dict."""
        settings = Settings()
        assert settings.engine_overrides == {}

    def test_default_window_dimensions(self):
        """Default window dimensions should have reasonable values."""
        settings = Settings()
        assert settings.window_width == 700
        assert settings.window_height == 500
        assert settings.window_x is None
        assert settings.window_y is None


class TestSettingsEngineOverrides:
    """Test engine override functionality."""

    def test_get_engine_for_extension_no_override(self):
        """Should return None when no override is set."""
        settings = Settings()
        assert settings.get_engine_for_extension("docx") is None

    def test_get_engine_for_extension_with_override(self):
        """Should return override when set."""
        settings = Settings(engine_overrides={"docx": "markitdown"})
        assert settings.get_engine_for_extension("docx") == "markitdown"

    def test_get_engine_for_extension_normalizes_input(self):
        """Should normalize extension (case insensitive, strip dot)."""
        settings = Settings(engine_overrides={"docx": "markitdown"})
        assert settings.get_engine_for_extension("DOCX") == "markitdown"
        assert settings.get_engine_for_extension(".docx") == "markitdown"
        assert settings.get_engine_for_extension(".DOCX") == "markitdown"

    def test_set_engine_for_extension(self):
        """Should set engine override correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            with patch.object(Settings, "config_path", return_value=config_path):
                settings = Settings()
                settings.set_engine_for_extension("docx", "pandoc")
                assert settings.engine_overrides["docx"] == "pandoc"

    def test_set_engine_normalizes_extension(self):
        """Should normalize extension when setting override."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            with patch.object(Settings, "config_path", return_value=config_path):
                settings = Settings()
                settings.set_engine_for_extension(".DOCX", "pandoc")
                assert "docx" in settings.engine_overrides
                assert settings.engine_overrides["docx"] == "pandoc"

    def test_reset_engine_override(self):
        """Should remove specific engine override."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            with patch.object(Settings, "config_path", return_value=config_path):
                settings = Settings(engine_overrides={"docx": "markitdown", "pdf": "pandoc"})
                settings.reset_engine_override("docx")
                assert "docx" not in settings.engine_overrides
                assert "pdf" in settings.engine_overrides

    def test_reset_engine_override_nonexistent(self):
        """Should not raise when resetting nonexistent override."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            with patch.object(Settings, "config_path", return_value=config_path):
                settings = Settings()
                # Should not raise
                settings.reset_engine_override("docx")
                assert settings.engine_overrides == {}

    def test_reset_all_engine_overrides(self):
        """Should clear all engine overrides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            with patch.object(Settings, "config_path", return_value=config_path):
                settings = Settings(engine_overrides={"docx": "markitdown", "pdf": "pandoc"})
                settings.reset_all_engine_overrides()
                assert settings.engine_overrides == {}


class TestSettingsPersistence:
    """Test settings save/load functionality."""

    def test_save_creates_directory(self):
        """Should create config directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "subdir" / "settings.json"
            with patch.object(Settings, "config_path", return_value=config_path):
                settings = Settings()
                settings.save()
                assert config_path.exists()

    def test_save_and_load_roundtrip(self):
        """Settings should survive save/load cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            with patch.object(Settings, "config_path", return_value=config_path):
                # Save settings
                original = Settings(
                    output_mode="folder",
                    output_folder="/tmp/output",
                    engine_overrides={"docx": "markitdown"},
                    window_width=800,
                    window_height=600,
                    window_x=100,
                    window_y=200,
                )
                original.save()

                # Load settings
                loaded = Settings.load()
                assert loaded.output_mode == "folder"
                assert loaded.output_folder == "/tmp/output"
                assert loaded.engine_overrides == {"docx": "markitdown"}
                assert loaded.window_width == 800
                assert loaded.window_height == 600
                assert loaded.window_x == 100
                assert loaded.window_y == 200

    def test_load_returns_defaults_when_file_missing(self):
        """Should return default settings if config file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.json"
            with patch.object(Settings, "config_path", return_value=config_path):
                settings = Settings.load()
                assert settings.output_mode == "same"
                assert settings.engine_overrides == {}

    def test_load_returns_defaults_on_invalid_json(self):
        """Should return default settings if config file contains invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            config_path.write_text("not valid json {{{")
            with patch.object(Settings, "config_path", return_value=config_path):
                settings = Settings.load()
                assert settings.output_mode == "same"
                assert settings.engine_overrides == {}

    def test_load_returns_defaults_on_extra_keys(self):
        """Should return defaults if JSON has unexpected keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            # Extra key that's not a valid Settings field
            config_path.write_text(json.dumps({"unknown_field": "value"}))
            with patch.object(Settings, "config_path", return_value=config_path):
                settings = Settings.load()
                # Should return defaults due to TypeError from unexpected kwarg
                assert settings.output_mode == "same"


class TestSettingsOutputMode:
    """Test output mode functionality."""

    def test_set_output_mode(self):
        """Should set output mode correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            with patch.object(Settings, "config_path", return_value=config_path):
                settings = Settings()
                settings.set_output_mode("folder")
                assert settings.output_mode == "folder"

    def test_set_output_folder(self):
        """Should set output folder correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            with patch.object(Settings, "config_path", return_value=config_path):
                settings = Settings()
                settings.set_output_folder("/home/user/documents")
                assert settings.output_folder == "/home/user/documents"

    def test_set_output_folder_to_none(self):
        """Should allow setting output folder to None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            with patch.object(Settings, "config_path", return_value=config_path):
                settings = Settings(output_folder="/some/path")
                settings.set_output_folder(None)
                assert settings.output_folder is None


class TestSettingsConfigPaths:
    """Test config path methods."""

    def test_config_path_is_json_file(self):
        """Config path should be a JSON file."""
        path = Settings.config_path()
        assert path.suffix == ".json"
        assert path.name == "settings.json"

    def test_config_dir_is_parent_of_config_path(self):
        """Config dir should be parent of config path."""
        assert Settings.config_dir() == Settings.config_path().parent
