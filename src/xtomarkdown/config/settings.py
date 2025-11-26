"""Settings management with cross-platform persistence."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from platformdirs import user_config_dir

APP_NAME = "xtomarkdown"


@dataclass
class Settings:
    """Application settings with JSON persistence."""

    # Output location mode: same folder as source, specific folder, or always ask
    output_mode: Literal["same", "folder", "ask"] = "same"

    # Specific output folder (used when output_mode is "folder")
    output_folder: str | None = None

    # User engine overrides per file extension
    # Maps extension (without dot) to engine name
    engine_overrides: dict[str, str] = field(default_factory=dict)

    # Window geometry (for restoring window position/size)
    window_width: int = 700
    window_height: int = 500
    window_x: int | None = None
    window_y: int | None = None

    @classmethod
    def config_dir(cls) -> Path:
        """Get the platform-specific config directory."""
        return Path(user_config_dir(APP_NAME))

    @classmethod
    def config_path(cls) -> Path:
        """Get the path to the settings JSON file."""
        return cls.config_dir() / "settings.json"

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from disk, or return defaults if not found."""
        path = cls.config_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return cls(**data)
            except (json.JSONDecodeError, TypeError, KeyError):
                # Return defaults on any parsing error
                pass
        return cls()

    def save(self) -> None:
        """Save settings to disk."""
        path = self.config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    def get_engine_for_extension(self, ext: str) -> str | None:
        """Get user's preferred engine for an extension, or None for default."""
        return self.engine_overrides.get(ext.lower().lstrip("."))

    def set_engine_for_extension(self, ext: str, engine: str) -> None:
        """Set preferred engine for an extension."""
        self.engine_overrides[ext.lower().lstrip(".")] = engine
        self.save()

    def reset_engine_override(self, ext: str) -> None:
        """Reset a single extension to use the default engine."""
        ext = ext.lower().lstrip(".")
        if ext in self.engine_overrides:
            del self.engine_overrides[ext]
            self.save()

    def reset_all_engine_overrides(self) -> None:
        """Reset all extensions to use default engines."""
        self.engine_overrides.clear()
        self.save()

    def set_output_mode(self, mode: Literal["same", "folder", "ask"]) -> None:
        """Set the output location mode."""
        self.output_mode = mode
        self.save()

    def set_output_folder(self, folder: str | None) -> None:
        """Set the specific output folder."""
        self.output_folder = folder
        self.save()
