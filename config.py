STARTUP_MODE_FILE_PATH = "/etc/prime_switcher/startup_mode"
DEFAULT_STARTUP_MODE = "inactive"


def read_startup_mode():

    try:
        with open(STARTUP_MODE_FILE_PATH, 'r') as f:
            content = f.read()
            if content in ["intel", "nvidia", "inactive", "nvidia_once"]:
                mode = content
            else:
                print("WARNING : Invalid startup mode in %s, defaulting to %s." % (STARTUP_MODE_FILE_PATH, DEFAULT_STARTUP_MODE))
                mode = DEFAULT_STARTUP_MODE
    except IOError:
        print("WARNING : Cannot read startup mode from %s, defaulting to %s." % (STARTUP_MODE_FILE_PATH, DEFAULT_STARTUP_MODE))
        mode = DEFAULT_STARTUP_MODE

    return mode


def write_startup_mode(mode):

    assert mode in ["intel", "nvidia", "inactive", "nvidia_once"]

    with open(STARTUP_MODE_FILE_PATH, 'w') as f:
        f.write(mode)
