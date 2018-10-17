import envs


def read_startup_mode():

    try:
        with open(envs.STARTUP_MODE_FILE_PATH, 'r') as f:
            content = f.read()
            if content in ["intel", "nvidia", "inactive", "nvidia_once", "backup"]:
                mode = content
            else:
                print("WARNING : Invalid startup mode in %s, defaulting to %s." % (envs.STARTUP_MODE_FILE_PATH, envs.DEFAULT_STARTUP_MODE))
                mode = envs.DEFAULT_STARTUP_MODE
    except IOError:
        print("WARNING : Cannot read startup mode from %s, defaulting to %s." % (envs.STARTUP_MODE_FILE_PATH, envs.DEFAULT_STARTUP_MODE))
        mode = envs.DEFAULT_STARTUP_MODE

    return mode


def write_startup_mode(mode):

    assert mode in ["intel", "nvidia", "inactive", "nvidia_once", "backup"]

    with open(envs.STARTUP_MODE_FILE_PATH, 'w') as f:
        f.write(mode)
