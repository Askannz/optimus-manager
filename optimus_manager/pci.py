from optimus_manager.detection import get_bus_ids


class PCIError(Exception):
    pass


def set_power_management(enabled):
    if enabled:
        _set_mode("auto")
    else:
        _set_mode("on")


def _set_mode(mode):

    bus_ids = get_bus_ids(notation_fix=False)
    pci_path = "/sys/bus/pci/devices/0000:%s/power/control" % bus_ids["nvidia"]

    try:
        with open(pci_path, "w") as f:
            f.write(mode)
    except FileNotFoundError:
        raise PCIError("Cannot find Nvidia PCI path at %s" % pci_path)
    except IOError:
        raise PCIError("Error writing to %s" % pci_path)
