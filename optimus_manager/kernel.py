import optimus_manager.checks as checks
import optimus_manager.pci as pci
from optimus_manager.bash import exec_bash, BashError


class KernelSetupError(Exception):
    pass


def setup_kernel_state(config, requested_gpu_mode):

    assert requested_gpu_mode in ["intel", "nvidia", "hybrid"]

    if requested_gpu_mode == "intel":
        _setup_intel_mode(config)

    elif requested_gpu_mode == "nvidia":
        _setup_nvidia_mode(config)
        
    elif requested_gpu_mode == "hybrid":
        _setup_hybrid_mode(config)

def _setup_intel_mode(config):

    # Resetting the Nvidia card to its base state
    _set_base_state(config)
    
    # Handling power switching according to the switching backend
    if config["optimus"]["switching"] == "nouveau":

        try:
            _load_nouveau(config)
        except KernelSetupError as e:
            print("ERROR : cannot load nouveau. Moving on. Error is : %s" % str(e))

    elif config["optimus"]["switching"] == "bbswitch":

        if not checks.is_module_available("bbswitch"):
            print("ERROR : module bbswitch is not available for the current kernel." 
                  " Is bbswitch or bbswitch-dkms installed ? Moving on...")

        else:
            try:
                _load_bbswitch()
            except KernelSetupError as e:
                print("ERROR : cannot load bbswitch. Moving on. Error is : %s" % str(e))
            else:
                _set_bbswitch_state("OFF")

    elif config["optimus"]["switching"] == "none":
        pass

    # Handling PCI power control
    if config["optimus"]["pci_power_control"] == "yes":
        if config["optimus"]["switching"] == "bbswitch":
            print("bbswitch is enabled, pci_power_control option ignored.")
        else:
            pci.set_power_state("auto")

def _setup_nvidia_mode(config):

    _set_base_state(config)
    _load_nvidia_modules(config)

def _setup_hybrid_mode(config):

    _set_base_state(config)
    _load_nvidia_modules(config)

def _set_base_state(config):

    # Base state :
    # - no kernel module loaded on the card
    # - bbswitch state to ON if bbswitch is loaded
    # - PCI power state to "on"

    _unload_nvidia_modules()
    _unload_nouveau()
    if checks.is_module_loaded("bbswitch"):
        _set_bbswitch_state("ON")
    pci.set_power_state("on")

    if config["optimus"]["pci_reset"] == "yes":
        pci.reset_nvidia()

def _load_nvidia_modules(config):

    print("Loading Nvidia modules")

    pat_value = _get_PAT_parameter_value(config)
    modeset_value = 1 if config["nvidia"]["modeset"] == "yes" else 0

    try:
        exec_bash("modprobe nvidia NVreg_UsePageAttributeTable=%d" % pat_value)
        exec_bash("modprobe nvidia_drm modeset=%d" % modeset_value)

    except BashError as e:
        raise KernelSetupError("Cannot load Nvidia modules : %s" % str(e))

def _unload_nvidia_modules():

    print("Unloading Nvidia modules")

    try:
        exec_bash("modprobe -r nvidia_drm nvidia_modeset nvidia_uvm nvidia")
    except BashError as e:
        raise KernelSetupError("Cannot unload Nvidia modules : %s" % str(e))

def _load_nouveau(config):

    print("Loading nouveau module")

    modeset_value = 1 if config["intel"]["modeset"] == "yes" else 0

    try:
        exec_bash("modprobe nouveau modeset=%d" % modeset_value)
    except BashError as e:
        raise KernelSetupError("Cannot load nouveau : %s" % str(e))

def _unload_nouveau():

    print("Unloading nouveau module")

    try:
        exec_bash("modprobe -r nouveau")
    except BashError as e:
        raise KernelSetupError("Cannot unload nouveau : %s" % str(e))

def _load_bbswitch():

    if not checks.is_module_available("bbswitch"):
        print("Module bbswitch not available for current kernel. Skipping bbswitch power switching.")
        return

    print("Loading bbswitch module")
    try:
        exec_bash("modprobe bbswitch")
    except BashError as e:
        raise KernelSetupError("Cannot load bbswitch : %s" % str(e))

def _get_PAT_parameter_value(config):

    pat_value = {"yes": 1, "no": 0}[config["nvidia"]["PAT"]]

    if not checks.is_pat_available():
        print("Warning : Page Attribute Tables are not available on your system.\n"
              "Disabling the PAT option for Nvidia.")
        pat_value = 0

    return pat_value

def _set_bbswitch_state(state):

    assert state in ["OFF", "ON"]

    print("Setting GPU power to %s via bbswitch" % state)

    try:
        with open("/proc/acpi/bbswitch", "w") as f:
            f.write(state)
    except FileNotFoundError:
        raise KernelSetupError("Cannot open /proc/acpi/bbswitch")
    except IOError:
        raise KernelSetupError("Error writing to /proc/acpi/bbswitch")
