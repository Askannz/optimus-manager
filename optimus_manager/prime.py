from optimus_manager.bash import exec_bash, BashError


def enable_PRIME():

    try:
        exec_bash("xrandr --setprovideroutputsource modesetting NVIDIA-0")
        exec_bash("xrandr --auto")
    except BashError:
        pass
