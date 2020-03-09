from . import var
from . import envs
from .kernel_parameters import get_kernel_parameters


def get_startup_mode():

    kernel_parameters = get_kernel_parameters()

    if kernel_parameters["startup_mode"] is None:
        try:
            startup_mode = var.read_startup_mode()
        except var.VarError as e:
            print("Cannot read startup mode : %s.\nUsing default startup mode %s instead." % (str(e), envs.DEFAULT_STARTUP_MODE))
            startup_mode = envs.DEFAULT_STARTUP_MODE

    else:
        print("Startup kernel parameter found : %s" % kernel_parameters["startup_mode"])
        startup_mode = kernel_parameters["startup_mode"]

    return startup_mode
