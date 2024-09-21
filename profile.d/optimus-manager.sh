#! /bin/bash

if [[ "${XDG_SESSION_TYPE}" == "wayland" ]] && [[ -x "/usr/bin/nvidia-persistenced" ]]; then
	export __GLX_VENDOR_LIBRARY_NAME="nvidia"
	export __VK_LAYER_NV_optimus="NVIDIA_only"
	# The Wayland display manager uses EGL instead, so it will still run on integrated graphics.
fi
