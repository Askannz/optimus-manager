#! /bin/bash

pkgname="optimus-manager-git"
install="optimus-manager.install"
pkgdesc="Allows using Nvidia Optimus laptop graphics"
license=("MIT")

#  PKGBUILD and program maintained at:
url="https://github.com/Askannz/optimus-manager"

epoch=1
pkgver=r763.01a04f9.python3.12
pkgrel=1
arch=("any")

source=("git+${url}.git")
sha1sums=("SKIP")


conflicts=(
	"bumblebee"
	"envycontrol"
	"nvidia-exec"
	"nvidia-switch"
	"nvidia-xrun"
	"optimus-manager"
	"switcheroo-control"
)


provides=(
	"optimus-manager=${pkgver}"
)


makedepends=(
	"git"
	"python-build"
	"python-installer"
	"python-setuptools"
	"python-wheel"
)


depends=(
	"dbus-python"
	"glxinfo"
	"NVIDIA-MODULE"
	"python"
	"xorg-xrandr"
)


optdepends=(
	'gdm-prime: needed if your login screen is gdm'
	'bbswitch: alternatively switches GPUs by using standard Optimus ACPI calls'
	'acpi_call: alternatively switches GPUs by brute forcing ACPI calls'
)


backup=(
	'etc/optimus-manager/nvidia-enable.sh'
	'etc/optimus-manager/nvidia-disable.sh'
	'etc/optimus-manager/optimus-manager.conf'
	'etc/optimus-manager/xorg/integrated-mode/integrated-gpu.conf'
	'etc/optimus-manager/xorg/nvidia-mode/integrated-gpu.conf'
	'etc/optimus-manager/xorg/nvidia-mode/nvidia-gpu.conf'
	'etc/optimus-manager/xorg/hybrid-mode/integrated-gpu.conf'
	'etc/optimus-manager/xorg/hybrid-mode/nvidia-gpu.conf'
	'etc/optimus-manager/xsetup-integrated.sh'
	'etc/optimus-manager/xsetup-nvidia.sh'
	'etc/optimus-manager/xsetup-hybrid.sh'
	'var/lib/optimus-manager/persistent/startup_mode'
)


SoftwareVersion () {
	cd "${srcdir}/optimus-manager"

	printf "r%s.%s" \
		"$(git rev-list --count HEAD)" \
		"$(git rev-parse --short=7 HEAD)"
}


PythonVersion () {
	pacman --sync --print-format "%v" python |
	cut --delimiter='.' --fields=1,2
}


pkgver () {
	local SoftwareVersion; SoftwareVersion="$(SoftwareVersion)"
	local PythonVersion; PythonVersion="$(PythonVersion)"

	if [[ -z "${SoftwareVersion}" ]]; then
		echo "Failed to retrieve: SoftwareVersion" >&2
		false
	elif [[ -z "${PythonVersion}" ]]; then
		echo "Failed to retrieve: PythonVersion" >&2
		false
	else
		printf "%s.python%s" \
			"${SoftwareVersion}" \
			"${PythonVersion}"
	fi
}


build () {
	cd "${srcdir}/optimus-manager"
	python3 setup.py build
}


package () {
	PackageFiles
	GeneratePyCache
}


PackageFiles () {
	PackageDefaultConf
	PackageEtc
	PackageLicense
	PackageLoginManagers
	PackageModprobe
	PackageProfile
	PackageSystemd
}


PackageDefaultConf () {
	install -Dm644 \
		"${srcdir}/optimus-manager/optimus-manager.conf" \
		"${pkgdir}/usr/share/optimus-manager/optimus-manager.conf"
}


PackageEtc () {
	cd "${srcdir}/optimus-manager/config"

	local Etc="${pkgdir}/etc/optimus-manager"
	local File
	local Files; readarray -t Files < <(
		find . -type f |
		cut --delimiter='/' --fields=2-
	)

	for File in "${Files[@]}"; do
		if echo "${File}" | grep --quiet --extended-regexp ".sh|.py"; then
			local Permissions=755
		else
			local Permissions=644
		fi

		install -Dm"${Permissions}" "${File}" "${Etc}/${File}"
	done
}


PackageLicense () {
	install -Dm644 \
		"${srcdir}/optimus-manager/LICENSE" \
		"${pkgdir}/usr/share/licenses/$pkgname/LICENSE"
}


PackageLoginManagers () {
	cd "${srcdir}/optimus-manager"

	install -Dm644 \
		login_managers/lightdm/20-optimus-manager.conf  \
		"${pkgdir}/etc/lightdm/lightdm.conf.d/20-optimus-manager.conf"

	install -Dm644 \
		login_managers/sddm/20-optimus-manager.conf \
		"${pkgdir}/etc/sddm.conf.d/20-optimus-manager.conf"
}


PackageModprobe () {
	install -Dm644 \
		"${srcdir}/optimus-manager/modules/optimus-manager.conf" \
		"${pkgdir}/usr/lib/modprobe.d/optimus-manager.conf"
}


PackageProfile () {
	install -Dm644 \
		"${srcdir}/optimus-manager/profile.d/optimus-manager.sh" \
		"${pkgdir}/etc/profile.d/optimus-manager.sh"
}


PackageSystemd () {
	cd "${srcdir}/optimus-manager"

	install -Dm644 \
		"systemd/optimus-manager.service" \
		"${pkgdir}/usr/lib/systemd/system/optimus-manager.service"

	install -Dm755 \
		"systemd/suspend/optimus-manager.py" \
		"${pkgdir}/usr/lib/systemd/system-sleep/optimus-manager.py"

	install -Dm644 \
		"systemd/logind/10-optimus-manager.conf" \
		"${pkgdir}/usr/lib/systemd/logind.conf.d/10-optimus-manager.conf"
}


GeneratePyCache () {
	cd "${srcdir}/optimus-manager"

	python3 setup.py install \
		--root="${pkgdir}" \
		--optimize=1 \
		--skip-build
}
