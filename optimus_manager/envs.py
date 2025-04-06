VERSION = "0"

LOG_DIR_PATH = "/var/log/optimus-manager"
SOCKET_PATH = "/tmp/optimus-manager"
SOCKET_TIMEOUT = 1.0

MODULES_UNLOAD_WAIT_MAX_TRIES = 5
MODULES_UNLOAD_WAIT_PERIOD = 1

DEFAULT_CONFIG_PATH = "/usr/share/optimus-manager/optimus-manager.conf"
USER_CONFIG_PATH = "/etc/optimus-manager/optimus-manager.conf"
XORG_CONF_PATH = "/etc/X11/xorg.conf.d/10-optimus-manager.conf"

NVIDIA_MANUAL_ENABLE_SCRIPT_PATH = "/etc/optimus-manager/nvidia-enable.sh"
NVIDIA_MANUAL_DISABLE_SCRIPT_PATH = "/etc/optimus-manager/nvidia-disable.sh"

PERSISTENT_VARS_FOLDER_PATH = "/var/lib/optimus-manager/persistent"
ACPI_CALL_STRING_VAR_PATH = "%s/acpi_call_strings.json" % PERSISTENT_VARS_FOLDER_PATH
TEMP_CONFIG_PATH_VAR_PATH = "%s/temp_conf_path" % PERSISTENT_VARS_FOLDER_PATH

TMP_VARS_FOLDER_PATH = "/var/lib/optimus-manager/tmp"
LAST_ACPI_CALL_STATE_VAR = "%s/last_acpi_call_state" % TMP_VARS_FOLDER_PATH
STATE_FILE_PATH = "%s/state.json" % TMP_VARS_FOLDER_PATH
USER_CONFIG_COPY_PATH = "%s/config_copy.conf" % TMP_VARS_FOLDER_PATH
CURRENT_DAEMON_RUN_ID = "%s/daemon_run_id" % TMP_VARS_FOLDER_PATH


EXTRA_XORG_OPTIONS_PATHS = {
    "hybrid-mode": {
        "integrated-gpu": "/etc/optimus-manager/xorg/hybrid-mode/integrated-gpu.conf",
        "nvidia-gpu"    : "/etc/optimus-manager/xorg/hybrid-mode/nvidia-gpu.conf"
    },
    "integrated-mode": {
        "integrated-gpu": "/etc/optimus-manager/xorg/integrated-mode/integrated-gpu.conf"
    },
    "nvidia-mode": {
        "integrated-gpu": "/etc/optimus-manager/xorg/nvidia-mode/integrated-gpu.conf",
        "nvidia-gpu"    : "/etc/optimus-manager/xorg/nvidia-mode/nvidia-gpu.conf"
    }
}


XSETUP_SCRIPTS_PATHS = {
    "hybrid": "/etc/optimus-manager/xsetup-hybrid.sh",
    "integrated": "/etc/optimus-manager/xsetup-integrated.sh",
    "nvidia": "/etc/optimus-manager/xsetup-nvidia.sh",
    "intel": "/etc/optimus-manager/xsetup-intel.sh" #DEPRECATED
}
