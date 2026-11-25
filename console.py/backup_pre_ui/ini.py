import configparser  # pip install configparser
import os


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")


def load_config():
    """Load the expected *idn response from the configuration file."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    if "Settings" in config:
        return config.get("Settings", "idn", fallback="LED Console 001")
    return "LED Console 001"
