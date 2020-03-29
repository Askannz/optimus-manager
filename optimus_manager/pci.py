import os
import re
from .bash import exec_bash, BashError
from .log_utils import get_logger

NVIDIA_VENDOR_ID = "10de"
INTEL_VENDOR_ID = "8086"

GPU_PCI_CLASS_PATTERN = "03[0-9a-f]{2}"
PCI_BRIDGE_PCI_CLASS_PATTERN = "0604"


class PCIError(Exception):
    pass


def set_power_state(mode):
    _write_to_nvidia_path("power/control", mode)

def get_power_state():
    return _read_from_nvidia_path("power/control")

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
        exec_bash("setpci -s %s 0x488.l=0x2000000:0x2000000" % nvidia_pci_bridge)
    except BashError as e:
        raise PCIError("failed to run setpci command : %s" % str(e))

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

    nvidia_ids_list = _get_bus_ids(match_pci_class=GPU_PCI_CLASS_PATTERN,
                                   match_vendor_id=NVIDIA_VENDOR_ID,
                                   notation_fix=notation_fix)

    intel_ids_list = _get_bus_ids(match_pci_class=GPU_PCI_CLASS_PATTERN,
                                  match_vendor_id=INTEL_VENDOR_ID,
                                  notation_fix=notation_fix)

    if len(nvidia_ids_list) > 1:
        logger.warning("Multiple Nvidia GPUs found ! Picking the first one.")

    if len(intel_ids_list) > 1:
        logger.warning("Multiple Intel GPUs found ! Picking the first one.")

    bus_ids = {}
    if len(nvidia_ids_list) > 0:
        bus_ids["nvidia"] = nvidia_ids_list[0]
    if len(intel_ids_list) > 0:
        bus_ids["intel"] = intel_ids_list[0]

    return bus_ids

def _get_bus_ids(match_pci_class, match_vendor_id, notation_fix=True):

    try:
        out = exec_bash("lspci -n")
    except BashError as e:
        raise PCIError("cannot run lspci -n : %s" % str(e))

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

    bus_ids = get_gpus_bus_ids(notation_fix=False)

    if "nvidia" not in bus_ids.keys():
        raise PCIError("Nvidia not in PCI bus")

    absolute_path = "/sys/bus/pci/devices/0000:%s/%s" % (bus_ids["nvidia"], relative_path)
    _write_to_pci_path(absolute_path, string)

def _read_from_nvidia_path(relative_path):

    bus_ids = get_gpus_bus_ids(notation_fix=False)

    if "nvidia" not in bus_ids.keys():
        raise PCIError("Nvidia not in PCI bus")

    absolute_path = "/sys/bus/pci/devices/0000:%s/%s" % (bus_ids["nvidia"], relative_path)
    return _read_pci_path(absolute_path)


def _write_to_pci_path(pci_path, string):

    try:
        with open(pci_path, "w") as f:
            f.write(string)
    except FileNotFoundError:
        raise PCIError("Cannot find PCI path at %s" % pci_path)
    except IOError:
        raise PCIError("Error writing to %s" % pci_path)

def _read_pci_path(pci_path):

    try:
        with open(pci_path, "r") as f:
            string = f.read()
    except FileNotFoundError:
        raise PCIError("Cannot find PCI path at %s" % pci_path)
    except IOError:
        raise PCIError("Error reading from %s" % pci_path)

    return string

def _get_connected_pci_bridges(pci_id):

    pci_bridges_ids_list = _get_bus_ids(match_pci_class=PCI_BRIDGE_PCI_CLASS_PATTERN,
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
