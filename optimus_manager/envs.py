VERSION = "0.8"

SOCKET_PATH = "/tmp/optimus-manager"
SOCKET_TIMEOUT = 1.0
STARTUP_MODE_VAR_PATH = "/var/lib/optimus-manager/startup_mode"
REQUESTED_MODE_VAR_PATH = "/var/lib/optimus-manager/requested_mode"
DPI_VAR_PATH = "/var/lib/optimus-manager/dpi"
DEFAULT_STARTUP_MODE = "intel"
SYSTEM_CONFIGS_PATH = "/etc/optimus-manager/configs/"
XORG_CONF_PATH = "/etc/X11/xorg.conf.d/10-optimus-manager.conf"

PRIME_SETUP_SCRIPT_PATH = "/usr/bin/optimus-manager_prime_setup"
X_STOP_SCRIPT_PATH = "/usr/bin/optimus-manager_X_stop"

SDDM_CONF_NAME = "10-optimus-manager.conf"
LIGHTDM_CONF_NAME = "10-optimus-manager.conf"
GDM_DESKTOP_FILE_NAME = "optimus-manager-xsetup.desktop"

DEFAULT_CONFIG_PATH = "/usr/share/optimus-manager.conf"
DEPRECATED_USER_CONFIG_PATH = "/etc/optimus-manager.conf"
USER_CONFIG_PATH = "/etc/optimus-manager/optimus-manager.conf"

EXTRA_XORG_OPTIONS_INTEL_PATH = "/etc/optimus-manager/xorg-intel.conf"
EXTRA_XORG_OPTIONS_NVIDIA_PATH = "/etc/optimus-manager/xorg-nvidia.conf"
