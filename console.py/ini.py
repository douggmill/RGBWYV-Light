import configparser  # pip install configparser
import os


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
DEFAULT_IDN = "LED Console 001"
DEFAULT_THEME = "dark"


def _read_config():
    """Read config.ini, always ensuring a Settings section exists."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if "Settings" not in config:
        config["Settings"] = {}
    return config


def load_config():
    """Load the expected *idn response from the configuration file."""
    config = _read_config()
    return config.get("Settings", "idn", fallback=DEFAULT_IDN)


def load_theme():
    """Load the saved UI theme. Missing or unknown values default to dark."""
    config = _read_config()
    theme = config.get("Settings", "theme", fallback=DEFAULT_THEME).strip().lower()
    if theme not in ("dark", "light"):
        return DEFAULT_THEME
    return theme


def save_theme(theme):
    """Write the UI theme back to config.ini without dropping other Settings keys."""
    theme = theme.strip().lower()
    if theme not in ("dark", "light"):
        theme = DEFAULT_THEME
    config = _read_config()
    if "idn" not in config["Settings"]:
        config["Settings"]["idn"] = DEFAULT_IDN
    config["Settings"]["theme"] = theme
    with open(CONFIG_FILE, "w") as handle:
        config.write(handle)
