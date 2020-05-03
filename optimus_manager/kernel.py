from . import envs
from . import var
from . import checks
from . import pci
from .acpi_data import ACPI_STRINGS
from .bash import exec_bash, BashError
from .log_utils import get_logger

class KernelSetupError(Exception):
    pass


def setup_kernel_state(config, prev_state, requested_mode):

    assert requested_mode in ["intel", "nvidia", "hybrid"]
    assert prev_state["type"] == "pending_pre_xorg_start"

    current_mode = prev_state["current_mode"]

    if current_mode in ["intel", None] and requested_mode in ["nvidia", "hybrid"]:
        _nvidia_up(config)

    elif current_mode in ["nvidia", "hybrid", None] and requested_mode == "intel":
        _nvidia_down(config)


def _nvidia_up(config):

    logger = get_logger()

    available_modules = _get_available_modules()
    logger.info("Available modules: %s", str(available_modules))

    _unload_nouveau(available_modules)

    switching_mode = config["optimus"]["switching"]
    if switching_mode == "bbswitch":
        _try_load_bbswitch(available_modules)
        _try_set_bbswitch_state("ON")
    elif switching_mode == "acpi_call":
        _try_load_acpi_call(available_modules)
        _try_set_acpi_call_state("ON")
    elif switching_mode == "custom":
        _try_custom_set_power_state("ON")

    if not pci.is_nvidia_visible():
        logger.info("Nvidia card not visible in PCI bus, rescanning")
        _try_rescan_pci()

    if config["optimus"]["pci_reset"] == "yes":
        _try_pci_reset(config, available_modules)

    if config["optimus"]["pci_power_control"] == "yes":
        _try_set_pci_power_state("on")

    _load_nvidia_modules(config, available_modules)

def _nvidia_down(config):

    logger = get_logger()

    available_modules = _get_available_modules()
    logger.info("Available modules: %s", str(available_modules))

    _unload_nvidia_modules(available_modules)

    switching_mode = config["optimus"]["switching"]
    if switching_mode == "nouveau":
        _try_load_nouveau(config, available_modules)
    elif switching_mode == "bbswitch":
        _try_load_bbswitch(available_modules)
        _set_bbswitch_state("OFF")
    elif switching_mode == "acpi_call":
        _try_load_acpi_call(available_modules)
        _try_set_acpi_call_state("OFF")
    elif switching_mode == "custom":
        _try_custom_set_power_state("OFF")


    if config["optimus"]["pci_remove"] == "yes":

        if switching_mode == "nouveau" or switching_mode == "bbswitch":
            logger.warning("%s is selected, pci_remove option ignored.", switching_mode)
        else:
            logger.info("Removing Nvidia from PCI bus")
            _try_remove_pci()


    if config["optimus"]["pci_power_control"] == "yes":

        switching_mode = config["optimus"]["switching"]
        if switching_mode == "bbswitch" or switching_mode == "acpi_call":
            logger.warning("%s is enabled, pci_power_control option ignored.", switching_mode)
        elif config["optimus"]["pci_remove"] == "yes":
            logger.warning("pci_remove is enabled, pci_power_control option ignored.")
        else:
            _try_set_pci_power_state("auto")


def _get_available_modules():
    MODULES = ["nouveau", "bbswitch", "acpi_call", "nvidia", "nvidia_drm", "nvidia_modeset", "nvidia_uvm"]
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

    logger = get_logger()

    try:
        _load_nouveau(config, available_modules)
    except KernelSetupError as e:
        logger.error(
            "Cannot load nouveau. Continuing anyways. Error is: %s", str(e))

def _try_load_bbswitch(available_modules):

    logger = get_logger()

    try:
        _load_module(available_modules, "bbswitch")
    except KernelSetupError as e:
        logger.error(
            "Cannot load bbswitch. Continuing anyways. Error is: %s", str(e))

def _try_load_acpi_call(available_modules):

    logger = get_logger()

    try:
        _load_module(available_modules, "acpi_call")
    except KernelSetupError as e:
        logger.error(
            "Cannot load acpi_call. Continuing anyway. Error is: %s", str(e))


def _unload_nvidia_modules(available_modules):
    _unload_modules(available_modules, ["nvidia_drm", "nvidia_modeset", "nvidia_uvm", "nvidia"])

def _unload_nouveau(available_modules):
    _unload_modules(available_modules, ["nouveau"])

def _try_unload_bbswitch(available_modules):

    logger = get_logger()

    try:
        _unload_modules(available_modules, ["bbswitch"])
    except KernelSetupError as e:
        logger.error(
            "Cannot unload bbswitch. Continuing anyway. Error is: %s", str(e))

def _unload_bbswitch(available_modules):
    _unload_modules(available_modules, ["bbswitch"])

def _load_module(available_modules, module, options=None):

    logger = get_logger()

    options = options or ""

    logger.info("Loading module %s", module)

    if module not in available_modules:
        raise KernelSetupError(
            "module %s is not available for current kernel."
            " Is the corresponding package installed ?" % module)
    try:
        exec_bash("modprobe %s %s" % (module, options))
    except BashError as e:
        raise KernelSetupError("error running modprobe for %s : %s" % (module, str(e)))

def _unload_modules(available_modules, modules_list):

    logger = get_logger()

    modules_to_unload = [m for m in modules_list if m in available_modules]

    if len(modules_to_unload) == 0:
        return

    logger.info("Unloading modules %s (if loaded)", str(modules_to_unload))

    try:
        # Unlike "rmmod", "modprobe -r" does not return an error if the module is not loaded.
        exec_bash("modprobe -r " + " ".join(modules_to_unload))
    except BashError as e:
        raise KernelSetupError("Cannot unload modules %s : %s" % (str(modules_to_unload), str(e)))


def _get_PAT_parameter_value(config):

    logger = get_logger()

    pat_value = {"yes": 1, "no": 0}[config["nvidia"]["pat"]]

    if not checks.is_pat_available():
        logger.warning(
            "Page Attribute Tables are not available on your system.\n"
            "Disabling the PAT option for Nvidia.")
        pat_value = 0

    return pat_value

def _set_bbswitch_state(state):

    logger = get_logger()

    assert state in ["OFF", "ON"]

    logger.info("Setting GPU power to %s via bbswitch", state)

    try:
        with open("/proc/acpi/bbswitch", "w") as f:
            f.write(state)
    except FileNotFoundError:
        raise KernelSetupError("Cannot open /proc/acpi/bbswitch")
    except IOError:
        raise KernelSetupError("Error writing to /proc/acpi/bbswitch")


def _set_acpi_call_state(state):

    logger = get_logger()

    assert state in ["OFF", "ON"]

    logger.info("Setting GPU power to %s via acpi_call", state)

    try:
        acpi_strings_list = var.read_acpi_call_strings()
        logger.info("Found saved ACPI strings")

    except var.VarError:
        acpi_strings_list = ACPI_STRINGS
        logger.info("No ACPI string saved, trying them all (expect kernel messages spam)")

    working_strings = []

    for off_str, on_str in acpi_strings_list:

        string = off_str if state == "OFF" else on_str

        try:
            logger.info("Sending ACPI string %s", string)
            with open("/proc/acpi/call", "w") as f:
                f.write(string)

            with open("/proc/acpi/call", "r") as f:
                output = f.read()
        except FileNotFoundError:
            raise KernelSetupError("Cannot open /proc/acpi/call")
        except IOError:
            continue

        if not "Error" in output:
            logger.info("ACPI string %s works, saving", string)
            working_strings.append((off_str, on_str))

    var.write_last_acpi_call_state(state)
    var.write_acpi_call_strings(working_strings)

def _try_remove_pci():

    logger = get_logger()

    try:
        pci.remove_nvidia()
    except pci.PCIError as e:
        logger.error(
            "Cannot remove Nvidia from PCI bus. Continuing anyways. Error is: %s", str(e))

def _try_rescan_pci():

    logger = get_logger()

    logger.info("Rescanning PCI bus")

    try:
        pci.rescan()
        if not pci.is_nvidia_visible():
            logger.error("Nvidia card not showing up in PCI bus after rescan. Continuing anyways.")
    except pci.PCIError as e:
        logger.error("Cannot rescan PCI bus. Continuing anyways. Error is: %s", str(e))

def _try_set_pci_power_state(state):

    logger = get_logger()

    logger.info("Setting Nvidia PCI power state to %s", state)

    try:
        pci.set_power_state(state)
    except pci.PCIError as e:
        logger.error(
            "Cannot set PCI power management state. Continuing anyways. Error is: %s", str(e))

def _try_pci_reset(config, available_modules):

    logger = get_logger()

    logger.info("Resetting Nvidia PCI device")

    try:
        _pci_reset(config, available_modules)
    except KernelSetupError as e:
        logger.error(
            "Nvidia PCI reset failed. Continuing anyways. Error is: %s", str(e))

def _try_set_acpi_call_state(state):

    logger = get_logger()

    try:
        _set_acpi_call_state(state)
    except KernelSetupError as e:
        logger.error(
            "Setting acpi_call to %s. Continuing anyways. Error is: %s",
            state, str(e))


def _try_set_bbswitch_state(state):

    logger = get_logger()

    try:
        _set_bbswitch_state(state)
    except KernelSetupError as e:
        logger.error(
            "Setting bbswitch to %s. Continuing anyways. Error is: %s",
            state, str(e))


def _pci_reset(config, available_modules):

    logger = get_logger()

    _unload_bbswitch(available_modules)

    try:
        if config["optimus"]["pci_reset"] == "function_level":
            logger.info("Performing function-level reset of Nvidia")
            pci.function_level_reset_nvidia()

        elif config["optimus"]["pci_reset"] == "hot_reset":
            logger.info("Starting hot reset sequence")
            pci.hot_reset_nvidia()

    except pci.PCIError as e:
        raise KernelSetupError("Failed to perform PCI reset : %s" % str(e))

def _try_custom_set_power_state(state):

    logger = get_logger()

    if state == "ON":
        script_path = envs.NVIDIA_MANUAL_ENABLE_SCRIPT_PATH
    elif state == "OFF":
        script_path = envs.NVIDIA_MANUAL_DISABLE_SCRIPT_PATH

    logger.info("Running custom power switching script %s", script_path)

    try:
        exec_bash(script_path)
    except BashError as e:
        logger.error(
            "Cannot run %s. Continuing anyways. Error is : %s",
            script_path, str(e))
