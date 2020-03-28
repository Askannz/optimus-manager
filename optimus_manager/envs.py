VERSION = "1.2.2"

SOCKET_PATH = "/tmp/optimus-manager"
SOCKET_TIMEOUT = 1.0

STARTUP_MODE_VAR_PATH = "/var/lib/optimus-manager/persistent/startup_mode"
ACPI_CALL_STRING_VAR_PATH = "/var/lib/optimus-manager/persistent/acpi_call_strings.json"
TEMP_CONFIG_PATH_VAR_PATH = "/var/lib/optimus-manager/persistent/temp_conf_path"
DAEMON_RUN_ID_GENERATOR_FILE_PATH = "/var/lib/optimus-manager/persistent/next_daemon_run_id"
SWITCH_ID_GENERATOR_FILE_PATH = "/var/lib/optimus-manager/persistent/next_switch_id"

LAST_ACPI_CALL_STATE_VAR = "/var/lib/optimus-manager/tmp/last_acpi_call_state"
STATE_FILE_PATH = "/var/lib/optimus-manager/tmp/state.json"
USER_CONFIG_COPY_PATH = "/var/lib/optimus-manager/tmp/config_copy.conf"
CURRENT_DAEMON_RUN_ID = "/var/lib/optimus-manager/tmp/daemon_run_id"

DEFAULT_STARTUP_MODE = "intel"

XORG_CONF_PATH = "/etc/X11/xorg.conf.d/10-optimus-manager.conf"

DEFAULT_CONFIG_PATH = "/usr/share/optimus-manager.conf"
USER_CONFIG_PATH = "/etc/optimus-manager/optimus-manager.conf"

EXTRA_XORG_OPTIONS_PATHS = {
    "intel": "/etc/optimus-manager/xorg-intel.conf",
    "nvidia": "/etc/optimus-manager/xorg-nvidia.conf",
    "hybrid": "/etc/optimus-manager/xorg-hybrid.conf"
}

XSETUP_SCRIPTS_PATHS = {
    "intel": "/etc/optimus-manager/xsetup-intel.sh",
    "nvidia": "/etc/optimus-manager/xsetup-nvidia.sh",
    "hybrid": "/etc/optimus-manager/xsetup-hybrid.sh"
}

NVIDIA_MANUAL_ENABLE_SCRIPT_PATH = "/etc/optimus-manager/nvidia-enable.sh"
NVIDIA_MANUAL_DISABLE_SCRIPT_PATH = "/etc/optimus-manager/nvidia-disable.sh"

LOG_DIR_PATH = "/var/log/optimus-manager/"
