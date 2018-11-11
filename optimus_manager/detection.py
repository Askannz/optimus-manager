from optimus_manager.bash import exec_bash

NVIDIA_VENDOR_ID = "10de"
INTEL_VENDOR_ID = "8086"


class DetectionError(Exception):
    pass


def get_bus_ids():

    # TODO : Return code error checking
    lspci_output = exec_bash("lspci -n").stdout.decode('utf-8')

    bus_ids = {}

    for line in lspci_output.splitlines():

        items = line.split(" ")
        bus_id = items[0].replace(".", ":")  # Notation quirk
        pci_class = items[1]
        vendor_id, product_id = items[2].split(":")

        # Display controllers are identified by a 03xx class
        if pci_class[:2] != "03":
            continue

        if vendor_id == NVIDIA_VENDOR_ID:
            if "nvidia" in bus_ids.keys():
                raise DetectionError("Multiple Nvidia GPUs found !")
            bus_ids["nvidia"] = bus_id

        elif vendor_id == INTEL_VENDOR_ID:
            if "intel" in bus_ids.keys():
                raise DetectionError("Multiple Intel GPUs found !")
            bus_ids["intel"] = bus_id

    if "nvidia" not in bus_ids.keys():
        raise DetectionError("Cannot find Nvidia GPU in PCI devices list.")

    if "intel" not in bus_ids.keys():
        raise DetectionError("Cannot find Intel GPU in PCI devices list.")

    return bus_ids


def get_login_managers():

    login_managers = []

    ret = exec_bash("which sddm").returncode
    if ret == 0:
        login_managers.append("sddm")

    ret = exec_bash("which gdm").returncode
    if ret == 0:
        login_managers.append("gdm")

    ret = exec_bash("which lightdm").returncode
    if ret == 0:
        login_managers.append("lightdm")

    return login_managers
