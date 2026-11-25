import configparser  # pip install configparser


CONFIG_FILE = "config.ini"


def load_config():
    """Load port and IDN from the configuration file."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    # Check if the section exists before accessing values
    if "Settings" in config:
        #port = config.get("Settings", "port", fallback="COM28")  # Default COM28
        idn1 = config.get("Settings", "idn", fallback="001")  # Default IDN 001
        return idn1  # , port
    else:
        return None, None  # Return defaults if no config file exists


# def save_config(port, idn):
#     """Save the given port and IDN to the configuration file."""
#     config = configparser.ConfigParser()
#
#     # Create 'Settings' section if it doesn't exist
#     if not config.has_section("Settings"):
#         config.add_section("Settings")
#
#     config["Settings"]["port"] = port  # Update values
#     config["Settings"]["idn"] = idn
#
#     # Write to file
#     with open(CONFIG_FILE, "w") as configfile:
#         config.write(configfile)
#
#     print(f"Configuration saved - Port: {port}, IDN: {idn}")