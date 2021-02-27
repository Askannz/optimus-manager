import os
from pathlib import Path
import re
import subprocess
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
        raise PCIError("Nvidia not in PCI bus")

    nvidia_pci_bridges_ids_list = _get_connected_pci_bridges(bus_ids["nvidia"])

    if len(nvidia_pci_bridges_ids_list) == 0:
        raise PCIError("PCI hot reset : cannot find PCI bridge connected to Nvidia card")

    if len(nvidia_pci_bridges_ids_list) > 1:
        raise PCIError("PCI hot reset : found more than one PCI bridge connected to Nvidia card")

    nvidia_pci_bridge = nvidia_pci_bridges_ids_list[0]

    logger.info("Removing Nvidia from PCI bridge")
    remove_nvidia()

    logger.info("Triggering PCI hot reset of bridge %s", nvidia_pci_bridge)
    try:
        subprocess.check_call(
            f"setpci -s {nvidia_pci_bridge} 0x488.l=0x2000000:0x2000000",
            shell=True, text=True, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise PCIError(f"Failed to run setpci command : {e.stderr}") from e

    logger.info("Rescanning PCI bus")
    rescan()

    if not is_nvidia_visible():
        raise PCIError("failed to bring Nvidia card back")

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
            logger.warning(f"Multiple {manufacturer} GPUs found ! Picking the first enumerated one.")

        if len(ids_list) > 0:
            bus_ids[manufacturer] = ids_list[0]

    if "intel" in bus_ids and "amd" in bus_ids:
        logger.warning("Found both an Intel and an AMD GPU. Defaulting to Intel.")
        del bus_ids["amd"]

    if not ("intel" in bus_ids or "amd" in bus_ids):
        raise PCIError("Cannot find the integrated GPU. Is this an Optimus system ?")

    return bus_ids

def _search_bus_ids(match_pci_class, match_vendor_id, notation_fix=True):

    try:
        out = subprocess.check_output(
            "lspci -n", shell=True, text=True, stderr=subprocess.PIPE).strip()
    except subprocess.CalledProcessError as e:
        raise PCIError(f"Cannot run lspci -n : {e.stderr}") from e

    bus_ids_list = []

    for line in out.splitlines():

        items = line.split(" ")

        bus_id = items[0]

        if notation_fix:
            # Xorg expects bus IDs separated by colons in decimal instead of
            # hexadecimal format without any leading zeroes and prefixed with
            # `PCI:`, so `3c:00:0` should become `PCI:60:0:0`
            bus_id = "PCI:" + ":".join(
                str(int(field, 16)) for field in re.split("[.:]", bus_id)
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
        raise PCIError("Nvidia not in PCI bus")

    nvidia_id = bus_ids["nvidia"]

    res = re.fullmatch(r"([0-9]{2}:[0-9]{2})\.[0-9]", nvidia_id)

    if res is None:
        raise PCIError(f"Unexpected PCI ID format: {nvidia_id}")

    partial_id = res.groups()[0]  # Bus ID minus the PCI function number

    # Applying to all PCI functions of the Nvidia card
    # (in case they have an audio chipset or a Thunderbolt controller, for instance)
    for device_path in Path("/sys/bus/pci/devices/").iterdir():

        device_id = device_path.name
        if re.fullmatch(f"0000:{partial_id}\\.([0-9])", device_id):

            write_path = device_path / relative_path
            logger.info(f"Writing \"{string}\" to {write_path}")
            _write_to_pci_path(write_path, string)


def _write_to_pci_path(pci_path, string):

    try:
        with open(pci_path, "w") as f:
            f.write(string)
    except FileNotFoundError as e:
        raise PCIError(f"Cannot find PCI path at {pci_path}") from e
    except IOError as e:
        raise PCIError(f"Error writing to {pci_path}: {str(e)}") from e

def _read_pci_path(pci_path):

    try:
        with open(pci_path, "r") as f:
            string = f.read()
    except FileNotFoundError as e:
        raise PCIError("Cannot find PCI path at %s" % pci_path) from e
    except IOError as e:
        raise PCIError("Error reading from %s" % pci_path) from e

    return string

def _get_connected_pci_bridges(pci_id):

    pci_bridges_ids_list = _search_bus_ids(
        match_pci_class=PCI_BRIDGE_PCI_CLASS_PATTERN,
        match_vendor_id=".+",
        notation_fix=False)

    connected_pci_bridges_ids_list = []

    for pci_bridge_id in pci_bridges_ids_list:

        absolute_path = "/sys/bus/pci/devices/0000:%s/" % pci_bridge_id

        for dir_name in os.listdir(absolute_path):
            dir_path = os.path.join(absolute_path, dir_name)

            if os.path.isdir(dir_path) and dir_name == "0000:%s" % pci_id:
                connected_pci_bridges_ids_list.append(pci_bridge_id)
                break

    return connected_pci_bridges_ids_list
