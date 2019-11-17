import re

def get_kernel_parameters():

    with open("/proc/cmdline", "r") as f:
        cmdline = f.read()

    for item in cmdline.split():
        if re.fullmatch("optimus-manager\\.startup=[^ ]+", item):
            startup_mode = item.split("=")[-1]
            if startup_mode not in ["intel", "nvidia", "hybrid"]:
                print("ERROR : invalid startup mode in kernel parameter : \"%s\". Ignored." % startup_mode)
                startup_mode = None
            break
    else:
        startup_mode = None

    return {"startup_mode": startup_mode}
