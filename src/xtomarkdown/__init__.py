"""XtoMarkdown - Cross-platform document to Markdown converter."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("xtomarkdown")
except PackageNotFoundError:
    # Package not installed (running from source without pip install -e)
    __version__ = "0.0.0-dev"
