#! /bin/bash

if [[ "${XDG_SESSION_TYPE}" == "wayland" ]] && [[ -x "/usr/bin/nvidia-persistenced" ]]; then
	export __GLX_VENDOR_LIBRARY_NAME="nvidia"
	export __VK_LAYER_NV_optimus="NVIDIA_only"
	# The desktop and most apps use EGL instead, so they will still run on the integrated GPU.
	# Check which apps are using the Nvidia GPU with `nvidia-smi`.
fi
