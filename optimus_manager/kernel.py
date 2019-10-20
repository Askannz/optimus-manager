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

    available_modules = _get_available_modules()
    print("Available kernel modules : %s" % str(available_modules))

    if requested_gpu_mode == "intel":
        _setup_intel_mode(config, available_modules)

    elif requested_gpu_mode == "nvidia":
        _setup_nvidia_mode(config, available_modules)

    elif requested_gpu_mode == "hybrid":
        _setup_hybrid_mode(config, available_modules)

def _setup_intel_mode(config, available_modules):

    # Resetting the system to its base state
    _set_base_state(config, available_modules)

    print("Setting up Intel state")

    # Power switching according to the switching backend
    if config["optimus"]["switching"] == "nouveau":
        _try_load_nouveau(config, available_modules)

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
            print("pci_remove is enabled, pci_power_control option ignored.")
        else:
            _try_set_pci_power_state("auto")

def _setup_nvidia_mode(config, available_modules):

    _set_base_state(config, available_modules)

    print("Setting up Nvidia state")
    _load_nvidia_modules(config, available_modules)

def _setup_hybrid_mode(config, available_modules):

    _set_base_state(config, available_modules)

    print("Setting up Hybrid state")
    _load_nvidia_modules(config, available_modules)

def _set_base_state(config, available_modules):

    print("Setting up base state")

    _unload_nvidia_modules(available_modules)
    _unload_nouveau(available_modules)

    switching_mode = config["optimus"]["switching"]
    if switching_mode == "bbswitch":
        _try_load_bbswitch(available_modules)
    elif switching_mode == "acpi_call":
        _try_load_acpi_call(available_modules)

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

    if switching_mode == "none":
        _try_custom_set_power_state("ON")

    if not pci.is_nvidia_visible():
        print("Nvidia card not visible in PCI bus, rescanning")
        _try_rescan_pci()

    if config["optimus"]["pci_reset"] != "no":
        _try_pci_reset(config, available_modules)

    if switching_mode == "bbswitch":
        # Re-loading bbswitch in case it was unloaded before PCI reset
        _try_load_bbswitch(available_modules)
    else:
        _try_unload_bbswitch(available_modules)

    _try_set_pci_power_state("on")


def _get_available_modules():
    MODULES = ["nouveau", "bbswitch", "acpi_call", "nvidia", "nvidia_drm", "nvidia_modeset"]
    return [module for module in MODULES if checks.is_module_available(module)]

def _load_nvidia_modules(config, available_modules):

    pat_value = _get_PAT_parameter_value(config)
    modeset_value = 1 if config["nvidia"]["modeset"] == "yes" else 0

    _load_module(available_modules, "nvidia", options="NVreg_UsePageAttributeTable=%d" % pat_value)
    _load_module(available_modules, "nvidia_drm", options="modeset=%d" % modeset_value)

def _load_nouveau(config, available_modules):
    modeset_value = 1 if config["intel"]["modeset"] == "yes" else 0
    _load_module(available_modules, "nouveau", options="modeset=%d" % modeset_value)

def _try_load_nouveau(config, available_modules):
    try:
        _load_nouveau(config, available_modules)
    except KernelSetupError as e:
        print("ERROR : cannot load nouveau. Continuing anyways. Error is : %s" %  str(e))

def _try_load_bbswitch(available_modules):
    try:
        _load_module(available_modules, "bbswitch")
    except KernelSetupError as e:
        print("ERROR : cannot load bbswitch. Continuing anyways. Error is : %s" %  str(e))

def _try_load_acpi_call(available_modules):
    try:
        _load_module(available_modules, "acpi_call")
    except KernelSetupError as e:
        print("ERROR : cannot load acpi_call. Continuing anyways. Error is : %s" %  str(e))


def _unload_nvidia_modules(available_modules):
    _unload_modules(available_modules, ["nvidia_drm", "nvidia_modeset", "nvidia_uvm", "nvidia"])

def _unload_nouveau(available_modules):
    _unload_modules(available_modules, ["nouveau"])

def _try_unload_bbswitch(available_modules):
    try:
        _unload_modules(available_modules, ["bbswitch"])
    except KernelSetupError as e:
        print("ERROR : cannot unload bbswitch. Continuing anyways. Error is : %s" %  str(e))

def _unload_bbswitch(available_modules):
    _unload_modules(available_modules, ["bbswitch"])

def _load_module(available_modules, module, options=None):

    options = options or ""

    print("Loading module %s" % module)

    if module not in available_modules:
        raise KernelSetupError("module %s is not available for current kernel."
                               " Is the corresponding package installed ?" % module)
    try:
        exec_bash("modprobe %s %s" % (module, options))
    except BashError as e:
        raise KernelSetupError("error running modprobe for %s : %s" % (module, str(e)))

def _unload_modules(available_modules, modules_list):

    modules_to_unload = [m for m in modules_list if m in available_modules]

    if len(modules_to_unload) == 0:
        return

    print("Unloading modules %s (if loaded)" % str(modules_to_unload))

    try:
        # Unlike "rmmod", "modprobe -r" does not return an error if the module is not loaded.
        exec_bash("modprobe -r " + " ".join(modules_to_unload))
    except BashError as e:
        raise KernelSetupError("Cannot unload modules %s : %s" % (str(modules_to_unload), str(e)))


def _get_PAT_parameter_value(config):

    pat_value = {"yes": 1, "no": 0}[config["nvidia"]["pat"]]

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

def _try_pci_reset(config, available_modules):

    try:
        _pci_reset(config, available_modules)
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

def _pci_reset(config, available_modules):

    _unload_bbswitch(available_modules)

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

    print("Running %s" % script_path)

    try:
        exec_bash(script_path)
    except BashError as e:
        print("ERROR : cannot run %s. Continuing anyways. Error is : %s"
              % (script_path, str(e)))
