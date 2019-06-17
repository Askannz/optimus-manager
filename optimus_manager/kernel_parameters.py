import re

def get_kernel_parameters():

    with open("/proc/cmdline", "r") as f:
        cmdline = f.read()

    for item in cmdline.split():
        if re.fullmatch("optimus-manager\\.startup=((nvidia)|(intel))", item):
            startup_mode = item.split("=")[-1]
            break
    else:
        startup_mode = None

    return {"startup_mode": startup_mode}
