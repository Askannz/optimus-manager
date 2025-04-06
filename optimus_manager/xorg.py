import os
import subprocess
import optimus_manager.checks as checks
import optimus_manager.envs as envs
from pathlib import Path
from .config import load_extra_xorg_options
from .log_utils import get_logger
from .pci import get_gpus_bus_ids


class XorgSetupError(Exception):
    pass


def configure_xorg(config, requested_gpu_mode):
    bus_ids = get_gpus_bus_ids()
    xorg_extra = load_extra_xorg_options()

    if requested_gpu_mode == "nvidia":
        xorg_conf_text = _generate_nvidia(config, bus_ids, xorg_extra)

    elif requested_gpu_mode == "integrated":
        xorg_conf_text = _generate_integrated(config, bus_ids, xorg_extra)

    elif requested_gpu_mode == "hybrid":
        xorg_conf_text = _generate_hybrid(config, bus_ids, xorg_extra)

    _remove_conflicting_confs()
    _write_xorg_conf(xorg_conf_text)


def cleanup_xorg_conf():
    _remove_conf(envs.XORG_CONF_PATH)


def is_xorg_running():
    return any([
        subprocess.run(
            f"pidof {name}", shell=True, stdout=subprocess.DEVNULL
        ).returncode == 0

        for name in ["X", "Xorg"]
    ])


def do_xsetup(requested_mode):
    logger = get_logger()

    if requested_mode == "nvidia":
        provider = checks.get_integrated_provider()
        logger.info("Running xrandr commands")

        try:
            for cmd in [
                (f"xrandr --setprovideroutputsource \"{provider}\" NVIDIA-0"),
                "xrandr --auto"
            ]:
                subprocess.check_call(
                    cmd, shell=True, text=True, stderr=subprocess.PIPE,
                    stdout=subprocess.DEVNULL)

        except subprocess.CalledProcessError as error:
            logger.error(f"Unable to setup Prime: xrandr error: {error.stderr}")

    script_path = _get_xsetup_script_path(requested_mode)
    logger.info("Running script: %s", script_path)

    try:
        subprocess.check_call(
            script_path, text=True, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)

    except subprocess.CalledProcessError as e:
        logger.error(f"Unable to run script: {script_path}: {e.stderr}")


def set_DPI(config):
    logger = get_logger()
    dpi_str = config["nvidia"]["dpi"]

    if dpi_str == "":
        return

    try:
        subprocess.check_call(
            f"xrandr --dpi {dpi_str}", shell=True, text=True,
            stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)

    except subprocess.CalledProcessError as error:
        logger.error(f"Unable to set DPI: xrandr error: {error.stderr}")


def _get_xsetup_script_path(requested_mode):
    logger = get_logger()

    if requested_mode == "integrated":
        bus_ids = get_gpus_bus_ids()

        if "intel" in bus_ids:
            if Path(envs.XSETUP_SCRIPTS_PATHS["intel"]).exists():
                script_name = "intel"

            else:
                script_name = "integrated"

        else:
            script_name = "integrated"

    elif requested_mode == "nvidia":
        script_name = "nvidia"

    elif requested_mode == "hybrid":
        script_name = "hybrid"

    else:
        assert False

    script_path = envs.XSETUP_SCRIPTS_PATHS[script_name]
    return script_path


def _generate_nvidia(config, bus_ids, xorg_extra):
    integrated_gpu = "intel" if "intel" in bus_ids else "amd"
    driver = "modesetting"

    if config[integrated_gpu]["driver"] != "modesetting" and config[integrated_gpu]["driver"] != "hybrid":

        if "intel" in bus_ids and checks.is_xorg_intel_module_available():
            driver = "intel"

        elif checks.is_xorg_amdgpu_module_available():
            driver = "amdgpu"

        else:
            driver = "modesetting"

    xorg_extra_nvidia = xorg_extra["nvidia-mode"]["nvidia-gpu"]
    xorg_extra_integrated = xorg_extra["nvidia-mode"]["integrated-gpu"]
    text = _make_modules_paths_section()

    text += "Section \"ServerLayout\"\n" \
            "\tIdentifier \"layout\"\n" \
            "\tScreen 0 \"nvidia\"\n" \
            "\tInactive \"integrated\"\n" \
            "EndSection\n\n"

    text += _make_nvidia_device_section(config, bus_ids, xorg_extra_nvidia)

    text += "Section \"Screen\"\n" \
            "\tIdentifier \"nvidia\"\n" \
            "\tDevice \"nvidia\"\n" \
            "\tOption \"AllowEmptyInitialConfiguration\"\n"

    if config["nvidia"]["allow_external_gpus"] == "yes":
        text += "\tOption \"AllowExternalGpus\"\n"

    text += "EndSection\n\n"

    text += "Section \"Device\"\n" \
            "\tIdentifier \"integrated\"\n" \
            "\tDriver \"%s\"\n" % driver

    if driver == "modesetting":
        text += "\tOption \"AccelMethod\" \"none\"\n"

    text += "\tBusID \"%s\"\n" % bus_ids[integrated_gpu]

    for line in xorg_extra_integrated:
        text += ("\t" + line + "\n")

    text += "EndSection\n\n"

    text += "Section \"Screen\"\n" \
            "\tIdentifier \"integrated\"\n" \
            "\tDevice \"integrated\"\n" \
            "EndSection\n\n"

    text += _make_server_flags_section(config)
    return text


def _generate_integrated(config, bus_ids, xorg_extra):
    xorg_extra_lines = xorg_extra["integrated-mode"]["integrated-gpu"]

    text = "Section \"ServerLayout\"\n" \
            "\tIdentifier \"layout\"\n" \
            "\tScreen 0 \"integrated\"\n" \
            "EndSection\n\n"

    text += "Section \"Monitor\"\n" \
            "\tIdentifier \"monitor0\"\n" \
            "EndSection\n\n"

    if "intel" in bus_ids:
        text += _make_intel_device_section(config, bus_ids, xorg_extra_lines)

    else:
        text += _make_amd_device_section(config, bus_ids, xorg_extra_lines)

    text += "Section \"Screen\"\n" \
            "\tIdentifier \"integrated\"\n" \
            "\tDevice \"integrated\"\n" \
            "\tMonitor \"monitor0\"\n" \
            "EndSection\n\n"

    return text


def _generate_hybrid(config, bus_ids, xorg_extra):
    xorg_extra_lines_integrated = xorg_extra["hybrid-mode"]["integrated-gpu"]
    xorg_extra_lines_nvidia = xorg_extra["hybrid-mode"]["nvidia-gpu"]
    text = _make_modules_paths_section()

    text += "Section \"ServerLayout\"\n" \
           "\tIdentifier \"layout\"\n" \
           "\tScreen 0 \"integrated\"\n" \
           "\tInactive \"nvidia\"\n" \
           "\tOption \"AllowNVIDIAGPUScreens\"\n" \
           "EndSection\n\n"

    if "intel" in bus_ids:
        text += _make_intel_device_section(config, bus_ids, xorg_extra_lines_integrated)

    else:
        text += _make_amd_device_section(config, bus_ids, xorg_extra_lines_integrated)

    text += "Section \"Screen\"\n" \
           "\tIdentifier \"integrated\"\n" \
           "\tDevice \"integrated\"\n"

    if config["nvidia"]["allow_external_gpus"] == "yes":
        text += "\tOption \"AllowExternalGpus\"\n"

    text += "EndSection\n\n"
    text += _make_nvidia_device_section(config, bus_ids, xorg_extra_lines_nvidia)

    text += "Section \"Screen\"\n" \
           "\tIdentifier \"nvidia\"\n" \
           "\tDevice \"nvidia\"\n" \
           "EndSection\n\n"

    text += _make_server_flags_section(config)
    return text


def _make_modules_paths_section():
    return "Section \"Files\"\n" \
           "\tModulePath \"/usr/lib/nvidia\"\n" \
           "\tModulePath \"/usr/lib32/nvidia\"\n" \
           "\tModulePath \"/usr/lib32/nvidia/xorg/modules\"\n" \
           "\tModulePath \"/usr/lib32/xorg/modules\"\n" \
           "\tModulePath \"/usr/lib64/nvidia/xorg/modules\"\n" \
           "\tModulePath \"/usr/lib64/nvidia/xorg\"\n" \
           "\tModulePath \"/usr/lib64/xorg/modules\"\n" \
           "EndSection\n\n"


def _make_nvidia_device_section(config, bus_ids, xorg_extra_lines):
    options = config["nvidia"]["options"].replace(" ", "").split(",")

    text = "Section \"Device\"\n" \
           "\tIdentifier \"nvidia\"\n" \
           "\tDriver \"nvidia\"\n"

    text += "\tBusID \"%s\"\n" % bus_ids["nvidia"]

    if "overclocking" in options:
        text += "\tOption \"Coolbits\" \"28\"\n"

    if "triple_buffer" in options:
        text += "\tOption \"TripleBuffer\" \"true\"\n"

    for line in xorg_extra_lines:
        text += ("\t" + line + "\n")

    text += "EndSection\n\n"
    return text


def _make_intel_device_section(config, bus_ids, xorg_extra_lines):
    logger = get_logger()

    if config["intel"]["driver"] == "intel" and not checks.is_xorg_intel_module_available():
        logger.warning("The Xorg module intel is not available. Defaulting to modesetting.")
        driver = "modesetting"

    elif config["intel"]["driver"] == "hybrid":
        driver = "intel"

    else:
        driver = config["intel"]["driver"]

    dri = int(config["intel"]["dri"])
    text = "Section \"Device\"\n" \
           "\tIdentifier \"integrated\"\n"
    text += "\tDriver \"%s\"\n" % driver
    text += "\tBusID \"%s\"\n" % bus_ids["intel"]

    if config["intel"]["accel"] != "":
        text += "\tOption \"AccelMethod\" \"%s\"\n" % config["intel"]["accel"]

    if config["intel"]["tearfree"] != "":
        tearfree_enabled_str = {"yes": "true", "no": "false"}[config["intel"]["tearfree"]]
        text += "\tOption \"TearFree\" \"%s\"\n" % tearfree_enabled_str

    if dri != 0:
        text += "\tOption \"DRI\" \"%d\"\n" % dri

    for line in xorg_extra_lines:
        text += ("\t" + line + "\n")

    text += "EndSection\n\n"
    return text


def _make_amd_device_section(config, bus_ids, xorg_extra_lines):
    logger = get_logger()

    if config["amd"]["driver"] == "amdgpu" and not checks.is_xorg_amdgpu_module_available():
        logger.warning("The Xorg module amdgpu is not available. Defaulting to modesetting.")
        driver = "modesetting"

    elif config["amd"]["driver"] == "hybrid":
        driver = "amdgpu"

    else:
        driver = config["amd"]["driver"]

    dri = int(config["amd"]["dri"])

    text = "Section \"Device\"\n" \
           "\tIdentifier \"integrated\"\n"

    text += "\tDriver \"%s\"\n" % driver
    text += "\tBusID \"%s\"\n" % bus_ids["amd"]

    if config["amd"]["tearfree"] != "":
        tearfree_enabled_str = {"yes": "true", "no": "false"}[config["amd"]["tearfree"]]
        text += "\tOption \"TearFree\" \"%s\"\n" % tearfree_enabled_str

    if dri != 0:
        text += "\tOption \"DRI\" \"%d\"\n" % dri

    for line in xorg_extra_lines:
        text += ("\t" + line + "\n")

    text += "EndSection\n\n"
    return text


def _make_server_flags_section(config):
    if config["nvidia"]["ignore_abi"] == "yes":
        return (
            "Section \"ServerFlags\"\n"
            "\tOption \"IgnoreABI\" \"1\"\n"
            "EndSection\n\n"
        )

    return ""


def _remove_conf(conf):
    try:
        os.remove(conf)

    except FileNotFoundError:
        pass


def _remove_conflicting_confs():
    _remove_conf("/etc/X11/xorg.conf")
    _remove_conf("/etc/X11/xorg.conf.d/90-mhwd.conf")


def _write_xorg_conf(xorg_conf_text):
    logger = get_logger()
    filepath = Path(envs.XORG_CONF_PATH)

    try:
        os.makedirs(filepath.parent, mode=0o755, exist_ok=True)

        with open(filepath, 'w') as writefile:
            logger.info("Writing Xorg conf: %s", envs.XORG_CONF_PATH)
            writefile.write(xorg_conf_text)

    except IOError as error:
        raise XorgSetupError("Unable to write Xorg conf: %s" % str(filepath)) from error
