"""File type to engine mapping utilities."""

from ..config.defaults import DEFAULT_ENGINE_MAPPING, SUPPORTED_FORMATS


def normalize_extension(extension: str) -> str:
    """
    Normalize a file extension to lowercase without leading dot.

    Args:
        extension: File extension (with or without leading dot, any case)

    Returns:
        Lowercase extension without dot (e.g., "docx")
    """
    return extension.lower().lstrip(".")


def get_engine_for_format(extension: str) -> str | None:
    """
    Get the default engine name for a file extension.

    Args:
        extension: File extension (with or without leading dot)

    Returns:
        Engine name or None if format is not supported
    """
    ext = normalize_extension(extension)
    mapping = DEFAULT_ENGINE_MAPPING.get(ext)
    if mapping:
        return mapping[0]  # First element is the default engine
    return None


def get_fallback_engine(extension: str) -> str | None:
    """
    Get the fallback engine name for a file extension.

    Args:
        extension: File extension (with or without leading dot)

    Returns:
        Fallback engine name or None if no fallback
    """
    ext = normalize_extension(extension)
    mapping = DEFAULT_ENGINE_MAPPING.get(ext)
    if mapping and len(mapping) > 1:
        return mapping[1]  # Second element is the fallback engine
    return None


def is_supported_format(extension: str) -> bool:
    """Check if a file extension is supported."""
    return normalize_extension(extension) in SUPPORTED_FORMATS


def get_supported_extensions() -> list[str]:
    """Get a list of all supported file extensions (without dots)."""
    return sorted(SUPPORTED_FORMATS)
