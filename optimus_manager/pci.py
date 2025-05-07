import os
import re
import subprocess
from pathlib import Path
from .log_utils import get_logger

VENDOR_IDS = {
    "nvidia": "10de",
    "intel": "8086",
    "amd": "1002"
}

GPU_PCI_CLASS_PATTERN = "03[0-9a-f]{2}"
PCI_BRIDGE_PCI_CLASS_PATTERN = "0604"


class PCIError(Exception):
    pass


def set_power_state(mode):
    _write_to_nvidia_path("power/control", mode)


def function_level_reset_nvidia():
    _write_to_nvidia_path("reset", "1")


def hot_reset_nvidia():
    logger = get_logger()
    bus_ids = get_gpus_bus_ids(notation_fix=False)

    if "nvidia" not in bus_ids.keys():
        raise PCIError("Nvidia isn't in the PCI bus")

    nvidia_pci_bridges_ids_list = _get_connected_pci_bridges(bus_ids["nvidia"])

    if len(nvidia_pci_bridges_ids_list) == 0:
        raise PCIError("Unable to PCI hot reset: Unable to find the PCI bridge connected to the Nvidia card")

    if len(nvidia_pci_bridges_ids_list) > 1:
        raise PCIError("Unable to PCI hot reset: Found more than one PCI bridge connected to the Nvidia card")

    nvidia_pci_bridge = nvidia_pci_bridges_ids_list[0]
    logger.info("Removing Nvidia from PCI bridge")
    remove_nvidia()
    logger.info("Triggering PCI hot reset of bridge: %s", nvidia_pci_bridge)

    try:
        subprocess.check_call(
            f"setpci -s {nvidia_pci_bridge} 0x488.l=0x2000000:0x2000000",
            shell=True, text=True, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)

    except subprocess.CalledProcessError as error:
        raise PCIError(f"Failed to run setpci: {e.stderr}") from error

    logger.info("Rescanning PCI bus")
    rescan()

    if not is_nvidia_visible():
        raise PCIError("Failed to bring the Nvidia card back")


def remove_nvidia():
    _write_to_nvidia_path("remove", "1")


def is_nvidia_visible():
    bus_ids = get_gpus_bus_ids(notation_fix=False)

    if "nvidia" not in bus_ids.keys():
        return False

    pci_path = "/sys/bus/pci/devices/0000:%s/" % bus_ids["nvidia"]
    return os.path.isdir(pci_path)


def rescan():
    _write_to_pci_path("/sys/bus/pci/rescan", "1")


def get_gpus_bus_ids(notation_fix=True):
    logger = get_logger()
    bus_ids = {}

    for manufacturer, vendor_id in VENDOR_IDS.items():
        ids_list = _search_bus_ids(
            match_pci_class=GPU_PCI_CLASS_PATTERN,
            match_vendor_id=vendor_id,
            notation_fix=notation_fix)

        if len(ids_list) > 1:
            logger.warning(f"Multiple {manufacturer} GPUs found: Picking the last one")

        if len(ids_list) > 0:
            bus_ids[manufacturer] = ids_list[-1]

    if "intel" in bus_ids and "amd" in bus_ids:
        logger.warning("Found both an Intel and an AMD GPU: Picking the Intel one")
        del bus_ids["amd"]

    elif not ("intel" in bus_ids or "amd" in bus_ids):
        logger.warning("No integrated GPU on: Using nvidia mode")

    return bus_ids


def _search_bus_ids(match_pci_class, match_vendor_id, notation_fix=True):
    try:
        out = subprocess.check_output(
            "lspci -n", shell=True, text=True, stderr=subprocess.PIPE).strip()

    except subprocess.CalledProcessError as error:
        raise PCIError(f"Unable to run lspci -n: {error.stderr}") from error

    bus_ids_list = []

    for line in out.splitlines():
        items = line.split(" ")
        bus_id = items[0]

        if notation_fix:
            # Example: `3c:00:0` (kernel hexadecimal) -> `PCI:60:0:0` (xorg decimal)

            # If there are devices with different number
            # `lspci -n` can sometimes output domain number

            bus_id = "PCI:" + ":".join(
                str(int(field, 16)) for field in re.split("[.:]", bus_id)[-3:]
            )

        pci_class = items[1][:-1]
        vendor_id, _ = items[2].split(":")

        if re.fullmatch(match_pci_class, pci_class) and re.fullmatch(match_vendor_id, vendor_id):
            bus_ids_list.append(bus_id)

    return bus_ids_list


def _write_to_nvidia_path(relative_path, string):
    logger = get_logger()
    bus_ids = get_gpus_bus_ids(notation_fix=False)

    if "nvidia" not in bus_ids.keys():
        raise PCIError("Nvidia isn't in the PCI bus")

    nvidia_id = bus_ids["nvidia"]
    res = re.fullmatch(r"([0-9]{2}:[0-9]{2})\.[0-9]", nvidia_id)

    if res is None:
        raise PCIError(f"Unexpected PCI ID format: {nvidia_id}")

    partial_id = res.groups()[0]
    # Bus ID minus the PCI function number

    # Applied to all PCI functions of the Nvidia card
    # in case they have an audio chipset or a Thunderbolt controller
    for device_path in Path("/sys/bus/pci/devices/").iterdir():
        device_id = device_path.name

        if re.fullmatch(f"0000:{partial_id}\\.([0-9])", device_id):
            write_path = device_path / relative_path
            logger.info(f"Writing \"{string}\" to: {write_path}")
            _write_to_pci_path(write_path, string)


def _write_to_pci_path(pci_path, string):
    try:
        with open(pci_path, "w") as pcifile:
            pcifile.write(string)

    except FileNotFoundError as error:
        raise PCIError(f"Unable to find PCI path: {pci_path}") from error

    except IOError as error:
        raise PCIError(f"Unable to write to PCI path: {pci_path}: {str(error)}") from error


def _read_pci_path(pci_path):
    try:
        with open(pci_path, "r") as pcifile:
            string = pcifile.read()

    except FileNotFoundError as error:
        raise PCIError("Unable to find PCI path: %s" % pci_path) from error

    except IOError as error:
        raise PCIError("Unable to read from PCI path: %s" % pci_path) from error

    return string


def _get_connected_pci_bridges(pci_id):
    bridges = _search_bus_ids(
        match_pci_class=PCI_BRIDGE_PCI_CLASS_PATTERN,
        match_vendor_id=".+",
        notation_fix=False)

    connected_bridges = []

    for bridge in bridges:
        path = "/sys/bus/pci/devices/0000:%s/" % bridge
        directories = os.listdir(path)
        index = 0

        while not connected_bridges and index < len(directories):
            dir_path = os.path.join(path, directories[index])

            if os.path.isdir(dir_path) and directories[index] == "0000:%s" % pci_id:
                connected_bridges.append(bridge)

            index += 1

    return connected_bridges
