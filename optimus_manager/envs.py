VERSION = "0.8"

SOCKET_PATH = "/tmp/optimus-manager"
SOCKET_TIMEOUT = 1.0

STARTUP_MODE_VAR_PATH = "/var/lib/optimus-manager/startup_mode"
REQUESTED_MODE_VAR_PATH = "/var/lib/optimus-manager/requested_mode"
DPI_VAR_PATH = "/var/lib/optimus-manager/dpi"

DEFAULT_STARTUP_MODE = "intel"

SYSTEM_CONFIGS_PATH = "/etc/optimus-manager/configs/"
XORG_CONF_PATH = "/etc/X11/xorg.conf.d/10-optimus-manager.conf"

DEFAULT_CONFIG_PATH = "/usr/share/optimus-manager.conf"
USER_CONFIG_PATH = "/etc/optimus-manager/optimus-manager.conf"

EXTRA_XORG_OPTIONS_INTEL_PATH = "/etc/optimus-manager/xorg-intel.conf"
EXTRA_XORG_OPTIONS_NVIDIA_PATH = "/etc/optimus-manager/xorg-nvidia.conf"

LOG_DIR_PATH = "/var/log/optimus-manager/"
BOOT_SETUP_LOGFILE_NAME = "boot_setup.log"
PRIME_SETUP_LOGFILE_NAME = "prime_setup.log"
GPU_SETUP_LOGFILE_NAME = "gpu_setup.log"
