VERSION = "1.2.2"

SOCKET_PATH = "/tmp/optimus-manager"
SOCKET_TIMEOUT = 1.0

STARTUP_MODE_VAR_PATH = "/var/lib/optimus-manager/startup_mode"
REQUESTED_MODE_VAR_PATH = "/var/lib/optimus-manager/requested_mode"
DPI_VAR_PATH = "/var/lib/optimus-manager/dpi"
TEMP_CONFIG_PATH_VAR_PATH = "/var/lib/optimus-manager/temp_conf_path"
ACPI_CALL_STRING_VAR_PATH = "/var/lib/optimus-manager/acpi_call_strings.json"
LAST_ACPI_CALL_STATE_VAR = "/var/lib/optimus-manager/last_acpi_call_state"

DEFAULT_STARTUP_MODE = "intel"

SYSTEM_CONFIGS_PATH = "/etc/optimus-manager/configs/"
XORG_CONF_PATH = "/etc/X11/xorg.conf.d/10-optimus-manager.conf"

DEFAULT_CONFIG_PATH = "/usr/share/optimus-manager.conf"
USER_CONFIG_PATH = "/etc/optimus-manager/optimus-manager.conf"
USER_CONFIG_COPY_PATH = "/var/lib/optimus-manager/config_copy.conf"

EXTRA_XORG_OPTIONS_INTEL_PATH = "/etc/optimus-manager/xorg-intel.conf"
EXTRA_XORG_OPTIONS_NVIDIA_PATH = "/etc/optimus-manager/xorg-nvidia.conf"

XSETUP_SCRIPT_INTEL = "/etc/optimus-manager/xsetup-intel.sh"
XSETUP_SCRIPT_NVIDIA = "/etc/optimus-manager/xsetup-nvidia.sh"

NVIDIA_MANUAL_ENABLE_SCRIPT_PATH = "/etc/optimus-manager/nvidia-enable.sh"
NVIDIA_MANUAL_DISABLE_SCRIPT_PATH = "/etc/optimus-manager/nvidia-disable.sh"

LOG_DIR_PATH = "/var/log/optimus-manager/"
BOOT_SETUP_LOGFILE_NAME = "boot_setup.log"
PRIME_SETUP_LOGFILE_NAME = "prime_setup.log"
GPU_SETUP_LOGFILE_NAME = "gpu_setup.log"
LOGGING_SEPARATOR_SUFFIX = " ==================== "
LOG_MAX_SIZE = 20000
LOG_CROPPED_SIZE = 10000
