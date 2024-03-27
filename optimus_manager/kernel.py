import time
import subprocess
from . import envs
from . import var
from . import checks
from . import pci
from .acpi_data import ACPI_STRINGS
from .log_utils import get_logger

class KernelSetupError(Exception):
    pass


def setup_kernel_state(config, prev_state, requested_mode):

    assert requested_mode in ["integrated", "nvidia", "hybrid"]
    assert prev_state["type"] == "pending_pre_xorg_start"

    current_mode = prev_state["current_mode"]

    if current_mode in ["integrated", None] and requested_mode in ["nvidia", "hybrid"]:
        _nvidia_up(config, hybrid=(requested_mode == "hybrid"))

    elif current_mode in ["nvidia", "hybrid", None] and requested_mode == "integrated":
        _nvidia_down(config)


def get_available_modules():

    MODULES = [
        "nouveau", "bbswitch", "acpi_call", "nvidia",
        "nvidia_drm", "nvidia_modeset", "nvidia_uvm"
    ]

    return [module for module in MODULES if checks.is_module_available(module)]

def nvidia_power_up(config, available_modules):

    logger = get_logger()

    switching_mode = config["optimus"]["switching"]
    if switching_mode == "bbswitch":
        _try_load_bbswitch(available_modules)
        _try_set_bbswitch_state("ON")
    elif switching_mode == "acpi_call":
        _try_load_acpi_call(available_modules)
        _try_set_acpi_call_state("ON")
    elif switching_mode == "custom":
        _try_custom_set_power_state("ON")
    else:
        logger.info("switching=%s, nothing to do", switching_mode)

def nvidia_power_down(config, available_modules):

    logger = get_logger()

    switching_mode = config["optimus"]["switching"]
    if switching_mode == "bbswitch":
        _try_load_bbswitch(available_modules)
        _set_bbswitch_state("OFF")
    elif switching_mode == "acpi_call":
        _try_load_acpi_call(available_modules)
        _try_set_acpi_call_state("OFF")
    elif switching_mode == "custom":
        _try_custom_set_power_state("OFF")
    else:
        logger.info("switching=%s, nothing to do", switching_mode)


def _nvidia_up(config, hybrid):

    logger = get_logger()

    available_modules = get_available_modules()
    logger.info("Available modules: %s", str(available_modules))

    _unload_nouveau(available_modules)

    nvidia_power_up(config, available_modules)

    if not pci.is_nvidia_visible():
        logger.info("Nvidia card not visible in PCI bus, rescanning")
        _try_rescan_pci()

    if config["optimus"]["pci_reset"] != "no":
        _try_pci_reset(config, available_modules)

    power_control = (
        config["optimus"]["pci_power_control"] == "yes" or \
        config["nvidia"]["dynamic_power_management"] != "no"
    )
    if power_control:
        _try_set_pci_power_state("auto" if hybrid else "on")

    _load_nvidia_modules(config, available_modules)

def _nvidia_down(config):

    logger = get_logger()

    available_modules = get_available_modules()
    logger.info("Available modules: %s", str(available_modules))

    _unload_nvidia_modules(available_modules)

    nvidia_power_down(config, available_modules)

    switching_mode = config["optimus"]["switching"]
    if switching_mode == "nouveau":
        _try_load_nouveau(config, available_modules)

    if config["optimus"]["pci_remove"] == "yes":

        if switching_mode == "nouveau" or switching_mode == "bbswitch":
            logger.warning("%s is selected, pci_remove option ignored.", switching_mode)
        else:
            logger.info("Removing Nvidia from PCI bus")
            _try_remove_pci()

    power_control = (
        config["optimus"]["pci_power_control"] == "yes" or \
        config["nvidia"]["dynamic_power_management"] != "no"
    )

    if power_control:

        switching_mode = config["optimus"]["switching"]
        if switching_mode == "bbswitch" or switching_mode == "acpi_call":
            logger.warning("%s is enabled, pci_power_control option ignored.", switching_mode)
        elif config["optimus"]["pci_remove"] == "yes":
            logger.warning("pci_remove is enabled, pci_power_control option ignored.")
        else:
            _try_set_pci_power_state("auto")


def _load_nvidia_modules(config, available_modules):

    logger = get_logger()


    #
    # nvidia module

    nvidia_options = []

    if config["nvidia"]["pat"] == "yes":

        if not checks.is_pat_available():
            logger.warning(
                "Page Attribute Tables are not available on your system.\n"
                "Disabling the PAT option for Nvidia.")
        else:
            nvidia_options.append("NVreg_UsePageAttributeTable=1")

    if config["nvidia"]["dynamic_power_management"] == "coarse":
        nvidia_options.append("NVreg_DynamicPowerManagement=0x01")
    elif config["nvidia"]["dynamic_power_management"] == "fine":
        nvidia_options.append("NVreg_DynamicPowerManagement=0x02")

    mem_th = config["nvidia"]["dynamic_power_management_memory_threshold"]
    if mem_th != "":
        nvidia_options.append(f"NVreg_DynamicPowerManagementVideoMemoryThreshold={mem_th}")

    _load_module(available_modules, "nvidia", options=nvidia_options)


    #
    # nvidia_drm module

    nvidia_drm_options = []

    if config["nvidia"]["modeset"] == "yes":
        nvidia_drm_options.append("modeset=1")

    _load_module(available_modules, "nvidia_drm", options=nvidia_drm_options)


def _load_nouveau(config, available_modules):
    # TODO: move that option to [optimus]
    nouveau_options = ["modeset=1"] if config["intel"]["modeset"] == "yes" else []
    _load_module(available_modules, "nouveau", options=nouveau_options)

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

    options = options or []

    logger.info("Loading module %s", module)

    if module not in available_modules:
        raise KernelSetupError(
            "module %s is not available for current kernel."
            " Is the corresponding package installed ?" % module)
    try:
        subprocess.check_call(
            f"modprobe {module} {' '.join(options)}",
            shell=True, text=True, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise KernelSetupError(f"Error running modprobe for {module}: {e.stderr}") from e

def _unload_modules(available_modules, modules_list):

    logger = get_logger()

    modules_to_unload = [m for m in modules_list if m in available_modules]

    if len(modules_to_unload) == 0:
        return

    logger.info("Unloading modules %s (if loaded)", str(modules_to_unload))

    counter = 0
    while True:

        counter += 1

        try:
            # We use "modprobe -r" because unlike "rmmod", it does not return an error if the module is not loaded.
            subprocess.check_call(
                f"modprobe -r {' '.join(modules_to_unload)}",
                shell=True, text=True, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)

        except subprocess.CalledProcessError as e:

            if counter > envs.MODULES_UNLOAD_WAIT_MAX_TRIES:
                logger.info(f"Max tries ({counter}) exceeded")
                raise KernelSetupError(f"Cannot unload modules {modules_to_unload}: {e.stderr}") from e
            else:
                logger.info(f"Cannot unload modules: {e.stderr}")
                logger.info(f"Waiting {envs.MODULES_UNLOAD_WAIT_PERIOD}s and retrying.")
                time.sleep(envs.MODULES_UNLOAD_WAIT_PERIOD)

        else:
            break


def _set_bbswitch_state(state):

    logger = get_logger()

    assert state in ["OFF", "ON"]

    logger.info("Setting GPU power to %s via bbswitch", state)

    try:
        with open("/proc/acpi/bbswitch", "w") as f:
            f.write(state)
    except FileNotFoundError as e:
        raise KernelSetupError("Cannot open /proc/acpi/bbswitch") from e
    except IOError as e:
        raise KernelSetupError("Error writing to /proc/acpi/bbswitch") from e


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
        except FileNotFoundError as e:
            raise KernelSetupError("Cannot open /proc/acpi/call") from e
        except IOError:
            continue

        if not "Error" in output:
            logger.info("ACPI string %s works, saving", string)
            working_strings.append((off_str, on_str))
            break

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
        raise KernelSetupError(f"Failed to perform PCI reset: {e}") from e

def _try_custom_set_power_state(state):

    logger = get_logger()

    if state == "ON":
        script_path = envs.NVIDIA_MANUAL_ENABLE_SCRIPT_PATH
    elif state == "OFF":
        script_path = envs.NVIDIA_MANUAL_DISABLE_SCRIPT_PATH

    logger.info("Running custom power switching script %s", script_path)

    try:
        subprocess.check_call(
            script_path, text=True, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        logger.error(f"Cannot run {script_path}. Continuing anyways. Error is: {e.stderr}")
