import subprocess
import time
from . import checks
from . import envs
from . import pci
from . import var
from .acpi_data import ACPI_STRINGS
from .log_utils import get_logger


class KernelSetupError(Exception):
    pass


def setup_kernel_state(config, prev_state, requested_mode):
    assert requested_mode in ["hybrid", "integrated", "nvidia"]
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
        logger.info("Skipping Nvidia power up: switching_mode=%s", switching_mode)


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
        logger.info("Skipping Nvidia power down: switching_mode=%s", switching_mode)


def _nvidia_up(config, hybrid):
    logger = get_logger()
    available_modules = get_available_modules()
    logger.info("Available modules: %s", str(available_modules))
    _unload_nouveau(available_modules)
    nvidia_power_up(config, available_modules)

    if not pci.is_nvidia_visible():
        logger.info("Nvidia card not visible in PCI bus: Rescanning...")
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
            logger.warning("Option ignored: pci_remove: due to switching_mode=%s", switching_mode)

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
            logger.warning("Option ignored: pci_power_control: due to switching_mode=%s", switching_mode)

        elif config["optimus"]["pci_remove"] == "yes":
            logger.warning("Option ignored: pci_power_control: due to pci_remove=enabled")

        else:
            _try_set_pci_power_state("auto")


def _load_nvidia_modules(config, available_modules):
    logger = get_logger()
    nvidia_options = []

    ### nvidia module

    if config["nvidia"]["pat"] == "yes" and checks.is_pat_available():
        nvidia_options.append("NVreg_UsePageAttributeTable=1")

    if config["nvidia"]["dynamic_power_management"] == "coarse":
        nvidia_options.append("NVreg_DynamicPowerManagement=0x01")

    elif config["nvidia"]["dynamic_power_management"] == "fine":
        nvidia_options.append("NVreg_DynamicPowerManagement=0x02")

    mem_th = config["nvidia"]["dynamic_power_management_memory_threshold"]

    if mem_th != "":
        nvidia_options.append(f"NVreg_DynamicPowerManagementVideoMemoryThreshold={mem_th}")

    _load_module(available_modules, "nvidia", options=nvidia_options)

    ### nvidia_drm module

    nvidia_drm_options = []

    if config["nvidia"]["modeset"] == "yes":
        nvidia_drm_options.append("modeset=1")

    _load_module(available_modules, "nvidia_drm", options=nvidia_drm_options)


def _load_nouveau(config, available_modules):
    # TODO: Move the option to [optimus]
    nouveau_options = ["modeset=1"] if config["intel"]["modeset"] == "yes" else []
    _load_module(available_modules, "nouveau", options=nouveau_options)


def _try_load_nouveau(config, available_modules):
    logger = get_logger()

    try:
        _load_nouveau(config, available_modules)

    except KernelSetupError as error:
        logger.error(
            "Unable to load nouveau: %s", str(error))


def _try_load_bbswitch(available_modules):
    logger = get_logger()

    try:
        _load_module(available_modules, "bbswitch")

    except KernelSetupError as error:
        logger.error(
            "Unable to load bbswitch: %s", str(error))


def _try_load_acpi_call(available_modules):
    logger = get_logger()

    try:
        _load_module(available_modules, "acpi_call")

    except KernelSetupError as error:
        logger.error(
            "Unable to load acpi_call: %s", str(error))


def _unload_nvidia_modules(available_modules):
    _unload_modules(available_modules, ["nvidia_drm", "nvidia_modeset", "nvidia_uvm", "nvidia"])


def _unload_nouveau(available_modules):
    _unload_modules(available_modules, ["nouveau"])


def _try_unload_bbswitch(available_modules):
    logger = get_logger()

    try:
        _unload_modules(available_modules, ["bbswitch"])

    except KernelSetupError as error:
        logger.error(
            "Unable to unload bbswitch: %s", str(error))


def _unload_bbswitch(available_modules):
    _unload_modules(available_modules, ["bbswitch"])


def _load_module(available_modules, module, options=None):
    logger = get_logger()
    options = options or []
    logger.info("Loading module: %s", module)

    if module not in available_modules:
        raise KernelSetupError(
            "Module not installed properly: %s" % module)

    try:
        subprocess.check_call(
            f"modprobe {module} {' '.join(options)}",
            shell=True, text=True, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)

    except subprocess.CalledProcessError as error:
        raise KernelSetupError(f"Failed to modprobe {module}: {error.stderr}") from error


def _unload_modules(available_modules, modules_list):
    logger = get_logger()
    modules_to_unload = [module for module in modules_list if module in available_modules]

    if len(modules_to_unload) == 0:
        return

    logger.info("Unloading modules: %s", str(modules_to_unload))
    counter = 0
    success = False

    while not success and counter < envs.MODULES_UNLOAD_WAIT_MAX_TRIES:
        counter += 1

        try:
            subprocess.check_call(
                f"modprobe -r {' '.join(modules_to_unload)}",
                shell=True, text=True, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)
            success = True

        except subprocess.CalledProcessError as error:
            if counter >= envs.MODULES_UNLOAD_WAIT_MAX_TRIES:
                logger.info(f"Max tries exceeded: {counter}")
                raise KernelSetupError(f"Failed to unload modules: {modules_to_unload}: {error.stderr}") from error

            else:
                logger.info(f"Failed to unload modules: {error.stderr}")
                logger.info(f"Waiting {envs.MODULES_UNLOAD_WAIT_PERIOD}s and retrying...")
                time.sleep(envs.MODULES_UNLOAD_WAIT_PERIOD)


def _set_bbswitch_state(state):
    logger = get_logger()
    assert state in ["OFF", "ON"]
    logger.info("Setting power via bbswitch to: %s", state)

    try:
        with open("/proc/acpi/bbswitch", "w") as bbfile:
            bbfile.write(state)

    except FileNotFoundError as error:
        raise KernelSetupError("Unable to open: /proc/acpi/bbswitch") from error

    except IOError as error:
        raise KernelSetupError("Unable to write to: /proc/acpi/bbswitch") from error


def _set_acpi_call_state(state):
    logger = get_logger()
    assert state in ["OFF", "ON"]
    logger.info("Setting power via acpi_call to: %s", state)

    try:
        acpi_strings_list = var.read_acpi_call_strings()

    except var.VarError:
        acpi_strings_list = ACPI_STRINGS
        logger.info("Trying all ACPI calls (may polute the kernel log)")

    working_strings = []

    for off_str, on_str in acpi_strings_list:
        if not working_strings:
            string = off_str if state == "OFF" else on_str

            try:
                logger.info("Sending ACPI call: %s", string)

                with open("/proc/acpi/call", "w") as callwrite:
                    callwrite.write(string)
                with open("/proc/acpi/call", "r") as callread:
                    output = callread.read()

            except FileNotFoundError as error:
                raise KernelSetupError("Unable to open: /proc/acpi/call") from error

            except IOError:
                continue

            if "Error" not in output:
                logger.info("Saving working ACPI call: %s", string)
                working_strings.append((off_str, on_str))

    var.write_last_acpi_call_state(state)
    var.write_acpi_call_strings(working_strings)


def _try_remove_pci():
    logger = get_logger()

    try:
        pci.remove_nvidia()

    except pci.PCIError as error:
        logger.error(
            "Unable to remove Nvidia from PCI bus: %s", str(error))


def _try_rescan_pci():
    logger = get_logger()

    try:
        pci.rescan()

        if not pci.is_nvidia_visible():
            logger.error("Nvidia card not showing up in PCI bus after rescan")

    except pci.PCIError as error:
        logger.error("Unable to rescan PCI bus: %s", str(error))


def _try_set_pci_power_state(state):
    logger = get_logger()
    logger.info("Setting Nvidia PCI power state to: %s", state)

    try:
        pci.set_power_state(state)

    except pci.PCIError as error:
        logger.error(
            "Unable to set PCI power state: %s", str(error))


def _try_pci_reset(config, available_modules):
    logger = get_logger()
    logger.info("Resetting Nvidia PCI device")

    try:
        _pci_reset(config, available_modules)

    except KernelSetupError as error:
        logger.error(
            "Unable to reset Nvidia PCI device: %s", str(error))


def _try_set_acpi_call_state(state):
    logger = get_logger()

    try:
        _set_acpi_call_state(state)

    except KernelSetupError as error:
        logger.error(
            "Unable to set acpi_call_sate to %s: %s", state, str(error))


def _try_set_bbswitch_state(state):
    logger = get_logger()

    try:
        _set_bbswitch_state(state)

    except KernelSetupError as error:
        logger.error(
            "Unable to set bbswitch_state to %s: %s", state, str(error))


def _pci_reset(config, available_modules):
    logger = get_logger()
    _unload_bbswitch(available_modules)

    try:
        if config["optimus"]["pci_reset"] == "function_level":
            logger.info("Performing function-level reset of Nvidia")
            pci.function_level_reset_nvidia()

        elif config["optimus"]["pci_reset"] == "hot_reset":
            logger.info("Starting hot reset of Nvidia")
            pci.hot_reset_nvidia()

    except pci.PCIError as error:
        raise KernelSetupError(f"Unable to perform PCI reset: {error}") from error


def _try_custom_set_power_state(state):
    logger = get_logger()

    if state == "ON":
        script_path = envs.NVIDIA_MANUAL_ENABLE_SCRIPT_PATH

    elif state == "OFF":
        script_path = envs.NVIDIA_MANUAL_DISABLE_SCRIPT_PATH

    logger.info("Running custom power switching script: %s", script_path)

    try:
        subprocess.check_call(
            script_path, text=True, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)

    except subprocess.CalledProcessError as error:
        logger.error(f"Unable to run power switching script: {error.stderr}")
