import optimus_manager.envs as envs
import optimus_manager.var as var
import optimus_manager.checks as checks
import optimus_manager.pci as pci
from optimus_manager.acpi_data import ACPI_STRINGS
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

    # Resetting the system to its base state
    _set_base_state(config)

    # Power switching according to the switching backend
    if config["optimus"]["switching"] == "nouveau":

        try:
            _load_nouveau(config)
        except KernelSetupError as e:
            print("ERROR : cannot load nouveau. Moving on. Error is : %s" % str(e))

    elif config["optimus"]["switching"] == "bbswitch":
        _set_bbswitch_state("OFF")

    elif config["optimus"]["switching"] == "acpi_call":
        _try_set_acpi_call_state("OFF")

    elif config["optimus"]["switching"] == "none":
        _try_custom_set_power_state("OFF")

    # PCI remove
    if config["optimus"]["pci_remove"] == "yes":

        switching_mode = config["optimus"]["switching"]
        if switching_mode == "nouveau" or switching_mode == "bbswitch":
            print("%s is selected, pci_remove option ignored." % switching_mode)
        else:
            print("Removing Nvidia from PCI bus")
            _try_remove_pci()

    # PCI power control
    if config["optimus"]["pci_power_control"] == "yes":

        switching_mode = config["optimus"]["switching"]
        if switching_mode == "bbswitch" or switching_mode == "acpi_call":
            print("%s is enabled, pci_power_control option ignored." % switching_mode)
        elif config["optimus"]["pci_remove"] == "yes":
            print("pci_remove is enabled, pci_power_control option ignored." % switching_mode)
        else:
            _try_set_pci_power_state("auto")

def _setup_nvidia_mode(config):

    _set_base_state(config)
    _load_nvidia_modules(config)

def _setup_hybrid_mode(config):

    _set_base_state(config)
    _load_nvidia_modules(config)
    
def _set_base_state(config):

    _unload_nvidia_modules()
    _unload_nouveau()

    switching_mode = config["optimus"]["switching"]

    try:
        if switching_mode == "bbswitch":
            _load_bbswitch()
        elif switching_mode == "acpi_call":
            _load_acpi_call()
    except KernelSetupError as e:
        print("ERROR : error loading modules for %s. Continuing anyways. Error is : %s" % (switching_mode, str(e)))
        if not checks.is_module_available(switching_mode):
            print("%s is not available for the current kernel. Is the corresponding package installed ?")

    if checks.is_module_loaded("bbswitch"):
        _try_set_bbswitch_state("ON")

    if checks.is_module_loaded("acpi_call"):

        try:
            last_acpi_call_state = var.read_last_acpi_call_state()
            should_send_acpi_call = (last_acpi_call_state == "OFF")
        except var.VarError:
            should_send_acpi_call = False

        if should_send_acpi_call:
            _try_set_acpi_call_state("ON")        

    if not pci.is_nvidia_visible():

        print("Nvidia card not visible in PCI bus, rescanning")
        _try_rescan_pci()

    _try_pci_reset(config)

    if switching_mode == "bbswitch":
        _load_bbswitch()
    else:
        _unload_bbswitch()

    if switching_mode == "none":
        _try_custom_set_power_state("ON")

    _try_set_pci_power_state("on")


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

    print("Unloading Nvidia modules (if any)")

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

    print("Unloading nouveau module (if any)")

    try:
        exec_bash("modprobe -r nouveau")
    except BashError as e:
        raise KernelSetupError("Cannot unload nouveau : %s" % str(e))

def _load_bbswitch():

    if not checks.is_module_available("bbswitch"):
        raise KernelSetupError("Module bbswitch not available for current kernel.")

    print("Loading bbswitch module")
    try:
        exec_bash("modprobe bbswitch")
    except BashError as e:
        raise KernelSetupError("Cannot load bbswitch : %s" % str(e))

def _unload_bbswitch():

    print("Unloading bbswitch module (if any)")

    try:
        exec_bash("modprobe -r bbswitch")
    except BashError as e:
        raise KernelSetupError("Cannot unload bbswitch : %s" % str(e))

def _load_acpi_call():

    if not checks.is_module_available("acpi_call"):
        raise KernelSetupError("Module acpi_call not available for current kernel.")

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
        acpi_strings_list = var.read_acpi_call_strings()
        print("Found saved ACPI strings")

    except var.VarError:
        acpi_strings_list = ACPI_STRINGS
        print("No ACPI string saved, trying them all (expect kernel messages spam)")

    working_strings = []

    for off_str, on_str in acpi_strings_list:

        string = off_str if state == "OFF" else on_str

        try:
            print("Sending ACPI string %s" % string)
            with open("/proc/acpi/call", "w") as f:
                f.write(string)

            with open("/proc/acpi/call", "r") as f:
                output = f.read()
        except FileNotFoundError:
            raise KernelSetupError("Cannot open /proc/acpi/call")
        except IOError:
            continue

        if not "Error" in output:
            print("ACPI string %s works, saving" % string)
            working_strings.append((off_str, on_str))

    var.write_last_acpi_call_state(state)
    var.write_acpi_call_strings(working_strings)

def _try_remove_pci():

    try:
        pci.remove_nvidia()
    except pci.PCIError as e:
        print("ERROR : cannot remove Nvidia from PCI bus. Continuing. Error is : %s" % str(e))

def _try_rescan_pci():

    try:
        pci.rescan()
        if not pci.is_nvidia_visible():
            print("ERROR : Nvidia card not showing up in PCI bus after rescan. Continuing anyways.")
    except pci.PCIError as e:
        print("ERROR : cannot rescan PCI bus. Continuing. Error is : %s" % str(e))

def _try_set_pci_power_state(state):

    try:
        pci.set_power_state(state)
    except pci.PCIError as e:
        print("ERROR : cannot set PCI power management state. Continuing. Error is : %s" % str(e))

def _try_pci_reset(config):

    try:
        _unload_bbswitch()
        _pci_reset(config)
    except KernelSetupError as e:
        print("ERROR : Nvidia PCI reset failed. Continuing. Error is : %s" % str(e))

def _try_set_acpi_call_state(state):

    try:
        _set_acpi_call_state(state)
    except KernelSetupError as e:
        print("ERROR : setting acpi_call to %s. Continuing anyways. Error is : %s" % (state, str(e)))


def _try_set_bbswitch_state(state):

    try:
        _set_bbswitch_state(state)
    except KernelSetupError as e:
        print("ERROR : setting bbswitch to %s. Continuing anyways. Error is : %s" % (state, str(e)))

def _pci_reset(config):

    if config["optimus"]["pci_reset"] == "no":
        return

    try:
        if config["optimus"]["pci_reset"] == "function_level":
            print("Performing function-level reset of Nvidia")
            pci.function_level_reset_nvidia()

        elif config["optimus"]["pci_reset"] == "hot_reset":

            print("Starting hot reset sequence")
            pci.hot_reset_nvidia()

    except pci.PCIError as e:
        raise KernelSetupError("Failed to perform PCI reset : %s" % str(e))

def _try_custom_set_power_state(state):

    if state == "ON":
        script_path = envs.NVIDIA_MANUAL_ENABLE_SCRIPT_PATH
    elif state == "OFF":
        script_path = envs.NVIDIA_MANUAL_DISABLE_SCRIPT_PATH

    try:
        exec_bash(script_path)
    except BashError as e:
        print("ERROR : cannot run %s. Continuing anyways. Error is : %s"
              % (script_path, str(e)))
