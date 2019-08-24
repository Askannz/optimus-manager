import re

from optimus_manager.bash import exec_bash, BashError

NVIDIA_VENDOR_ID = "10de"
INTEL_VENDOR_ID = "8086"


class PCIError(Exception):
    pass


def set_power_management(enabled):

    if enabled:
        _write_to_pci("power/control", "auto")
    else:
        _write_to_pci("power/control", "on")

def reset_nvidia():
    _write_to_pci("reset", "1")


def get_bus_ids(notation_fix=True):

    try:
        lspci_output = exec_bash("lspci -n").stdout.decode('utf-8')
    except BashError as e:
        raise PCIError("cannot run lspci -n : %s" % str(e))

    bus_ids = {}

    for line in lspci_output.splitlines():

        items = line.split(" ")

        bus_id = items[0]

        if notation_fix:
            # Xorg expects bus IDs separated by colons in decimal instead of
            # hexadecimal format without any leading zeroes and prefixed with
            # `PCI:`, so `3c:00:0` should become `PCI:60:0:0`
            bus_id = "PCI:" + ":".join(
                str(int(field, 16)) for field in re.split("[.:]", bus_id)
            )

        pci_class = items[1]
        vendor_id, product_id = items[2].split(":")

        # Display controllers are identified by a 03xx class
        if pci_class[:2] != "03":
            continue

        if vendor_id == NVIDIA_VENDOR_ID:
            if "nvidia" in bus_ids.keys():
                raise PCIError("Multiple Nvidia GPUs found !")
            bus_ids["nvidia"] = bus_id

        elif vendor_id == INTEL_VENDOR_ID:
            if "intel" in bus_ids.keys():
                raise PCIError("Multiple Intel GPUs found !")
            bus_ids["intel"] = bus_id

    if "nvidia" not in bus_ids.keys():
        raise PCIError("Cannot find Nvidia GPU in PCI devices list.")

    if "intel" not in bus_ids.keys():
        raise PCIError("Cannot find Intel GPU in PCI devices list.")

    return bus_ids


def _write_to_pci(relative_path, string):

    bus_ids = get_bus_ids(notation_fix=False)
    pci_path = "/sys/bus/pci/devices/0000:%s/%s" % (bus_ids["nvidia"], relative_path)

    try:
        with open(pci_path, "w") as f:
            f.write(string)
    except FileNotFoundError:
        raise PCIError("Cannot find Nvidia PCI path at %s" % pci_path)
    except IOError:
        raise PCIError("Error writing to %s" % pci_path)
