import optimus_manager.checks as checks
import optimus_manager.pci as pci
from optimus_manager.acpi_data import ACPI_METHODS
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
                if config["optimus"]["pci_remove"] == "yes":
                    pci.remove_nvidia()
                _set_bbswitch_state("OFF")

    elif config["optimus"]["switching"] == "acpi_call":

        if not checks.is_module_available("acpi_call"):
            print("ERROR : module acpi_call is not available for the current kernel." 
                  " Is acpi_call or acpi_call-dkms installed ? Moving on...")

        else:
            try:
                _load_acpi_call()
            except KernelSetupError as e:
                print("ERROR : cannot load acpi_call. Moving on. Error is : %s" % str(e))
            else:
                if config["optimus"]["pci_remove"] == "yes":
                    pci.remove_nvidia()
                _set_acpi_call_state("OFF")

    elif config["optimus"]["switching"] == "none":
        pass

    # Handling PCI power control
    if config["optimus"]["pci_power_control"] == "yes":
        if config["optimus"]["switching"] == "bbswitch":
            print("bbswitch is enabled, pci_power_control option ignored.")
        elif config["optimus"]["switching"] == "acpi_call":
            print("acpi_call is enabled, pci_power_control option ignored.")
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

    if not pci.is_nvidia_visible():

        print("Nvidia card not visible in PCI bus")

        if checks.is_module_loaded("bbswitch"):
            _set_bbswitch_state("ON")

        # Unlike bbswitch, It's better to ignore acpi_call altogether if the config
        # file does not ask for it. The user could have this module loaded for other purposes,
        # and we don't want to fire a volley of ACPI commands unless strictly necessary.
        if checks.is_module_loaded("acpi_call") and \
        config["optimus"]["switching"] == "acpi_call":
            _set_acpi_call_state("ON")

        print("Rescanning PCI bus")
        pci.rescan()

        _pci_reset(config)

        if not pci.is_nvidia_visible():
            raise KernelSetupError("Rescanning Nvidia PCI device failed")

    else:

        if checks.is_module_loaded("bbswitch"):
            _set_bbswitch_state("ON")
        if checks.is_module_loaded("acpi_call") and \
        config["optimus"]["switching"] == "acpi_call":
            _set_acpi_call_state("ON")

        _pci_reset(config)

    pci.set_power_state("on")


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
        print("Module bbswitch not available for current kernel.")
        return

    print("Loading bbswitch module")
    try:
        exec_bash("modprobe bbswitch")
    except BashError as e:
        raise KernelSetupError("Cannot load bbswitch : %s" % str(e))

def _load_acpi_call():

    if not checks.is_module_available("acpi_call"):
        print("Module acpi_call not available for current kernel.")
        return

    print("Loading acpi_call module")
    try:
        exec_bash("modprobe acpi_call")
    except BashError as e:
        raise KernelSetupError("Cannot load acpi_call : %s" % str(e))

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

def _set_acpi_call_state(state):

    assert state in ["OFF", "ON"]

    print("Setting GPU power to %s via acpi_call" % state)

    try:
        for off_str, on_str in ACPI_METHODS:
            string = off_str if state == "OFF" else on_str
            with open("/proc/acpi/call", "w") as f:
                f.write(string)
    except FileNotFoundError:
        raise KernelSetupError("Cannot open /proc/acpi/call")
    except IOError:
        raise KernelSetupError("Error writing to /proc/acpi/call")

def _pci_reset(config):

    if config["optimus"]["pci_reset"] == "no":
        return

    try:
        if config["optimus"]["pci_reset"] == "function_level":
            print("Performing function-level reset of Nvidia")
            pci.function_level_reset_nvidia()

        elif config["optimus"]["pci_reset"] == "hot_reset":

            if config["optimus"]["pci_remove"] == "no":
                print("Option pci_reset=hot_reset ignored because pci_remove=no. Not resetting.")
                return

            print("Performing hot reset of PCI bridge")
            pci.hot_reset_nvidia()

    except pci.PCIError as e:
        print("Failed to perform PCI reset : %s" % str(e))
