#! /bin/bash
set -e

if [[ "${XDG_SESSION_TYPE}" == "wayland" ]] &&
[[ -z "${__NV_PRIME_RENDER_OFFLOAD}" ]]; then
	__NV_PRIME_RENDER_OFFLOAD="$(
		lspci |
		grep --extended-regexp --ignore-case "vga|3d" |
		grep --line-number "NVIDIA" |
		cut --delimiter=":" --fields=1 |
		head -n1
	)"

	if [[ -z "${__NV_PRIME_RENDER_OFFLOAD}" ]]; then
		unset __NV_PRIME_RENDER_OFFLOAD
	else
		export __NV_PRIME_RENDER_OFFLOAD
		export __GLX_VENDOR_LIBRARY_NAME="nvidia"
		export __VK_LAYER_NV_optimus="NVIDIA_only"
	fi
fi
