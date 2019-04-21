import optimus_manager.checks as checks
import optimus_manager.pci as pci
from optimus_manager.bash import exec_bash, BashError


class KernelSetupError(Exception):
    pass


def setup_kernel_state(config, requested_gpu_mode):

    assert requested_gpu_mode in ["intel", "nvidia"]

    if requested_gpu_mode == "intel":
        _unload_nvidia_modules(config)
        _power_switch_off(config)

    elif requested_gpu_mode == "nvidia":
        _power_switch_on(config)
        _load_nvidia_modules(config)


def _load_nvidia_modules(config):

    print("Loading Nvidia modules")

    pat_value = _get_PAT_parameter_value(config)

    try:
        exec_bash("modprobe nvidia NVreg_UsePageAttributeTable=%d" % pat_value)
        if config["nvidia"]["modeset"] == "yes":
            exec_bash("modprobe nvidia_drm modeset=1")
        else:
            exec_bash("modprobe nvidia_drm modeset=0")

    except BashError as e:
        raise KernelSetupError("Cannot load Nvidia modules : %s" % str(e))


def _unload_nvidia_modules(config):

    print("Unloading Nvidia modules")

    try:
        exec_bash("modprobe -r nvidia_drm nvidia_modeset nvidia_uvm nvidia")
    except BashError as e:
        raise KernelSetupError("Cannot unload Nvidia modules : %s" % str(e))


def _get_PAT_parameter_value(config):

    pat_value = {"yes": 1, "no": 0}[config["nvidia"]["PAT"]]

    if not checks.is_pat_available():
        print("Warning : Page Attribute Tables are not available on your system.\n"
              "Disabling the PAT option for Nvidia.")
        pat_value = 0

    return pat_value


def _power_switch_off(config):

    # Modules

    if config["optimus"]["switching"] == "bbswitch":
        _load_bbswitch()
        _set_bbswitch_mode("OFF")

    elif config["optimus"]["switching"] == "nouveau":
        _load_nouveau(config)

    else:
        print("Power switching backend is disabled.")

    # PCI power management

    if config["optimus"]["pci_power_control"] == "yes":

        if config["optimus"]["switching"] == "bbswitch":
            print("bbswitch is enabled, pci_power_control option ignored.")
        else:
            _set_PCI_power_mode("OFF")


def _power_switch_on(config):

    # Modules

    _unload_nouveau()

    if config["optimus"]["switching"] == "bbswitch":
        _load_bbswitch()
        _set_bbswitch_mode("ON")

    else:
        print("Power switching backend is disabled.")

    # PCI power management
    if config["optimus"]["pci_power_control"] == "yes":

        if config["optimus"]["switching"] == "bbswitch":
            print("bbswitch is enabled, pci_power_control option ignored.")
        else:
            _set_PCI_power_mode("ON")


def _load_bbswitch():

    if not checks.is_module_available("bbswitch"):
        print("Module bbswitch not available for current kernel. Skipping bbswitch power switching.")

    else:
        print("Loading bbswitch module")
        try:
            exec_bash("modprobe bbswitch")
        except BashError as e:
            raise KernelSetupError("Cannot load bbswitch : %s" % str(e))


def _set_bbswitch_mode(requested_gpu_state):

    assert requested_gpu_state in ["OFF", "ON"]

    print("Setting GPU power to %s via bbswitch" % requested_gpu_state)
    exec_bash("echo %s | tee /proc/acpi/bbswitch" % requested_gpu_state)

    current_gpu_state = ("ON" if checks.is_gpu_powered() else "OFF")

    if current_gpu_state != requested_gpu_state:
        raise KernelSetupError("bbswitch failed to set the GPU to %s" % requested_gpu_state)
    else:
        print("bbswitch reports that the GPU is %s" % current_gpu_state)


def _load_nouveau(config):

    modeset_value = {"yes": 1, "no": 0}[config["intel"]["modeset"]]

    print("Loading nouveau module")

    try:
        exec_bash("modprobe nouveau modeset=%d" % modeset_value)
    except BashError as e:
        raise KernelSetupError("Cannot load nouveau : %s" % str(e))


def _unload_nouveau(config):

    try:
        exec_bash("modprobe -r nouveau")
    except BashError as e:
        raise KernelSetupError("Cannot unload nouveau : %s" % str(e))


def _set_PCI_power_mode(requested_gpu_state):

    assert requested_gpu_state in ["OFF", "ON"]

    try:
        pci.set_power_management((requested_gpu_state == "OFF"))
    except pci.PCIError as e:
        print("WARNING : Cannot set PCI power management : %s" % str(e))
