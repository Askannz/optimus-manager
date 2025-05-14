#! /bin/bash
set -e

here="$(realpath "$(dirname "${0}")")"


mainFunction () {
	sudo -v
	so rm --force "${here}/"*.pkg.*
	syncSrc
	makePackage
}


checkRequiredSoftware () {
	if [[ ! -x "/usr/bin/rsync" ]]; then
		echo "Not installed: rsync" >&2
		exit 1
	fi
}


makePackage () {
	cd "${here}"

	export PACMAN_AUTH="sudo"
	export PACKAGER="${USER} <@${HOSTNAME}>"
	so makepkg --needed --noconfirm --noextract --syncdeps --skipinteg --rmdeps
}


so () {
	local commands="${*}"

	if [[ "${verbose}" -eq 1 ]]; then
		if ! ${commands}; then
			exit "${?}"
		fi
	elif ! error="$(eval "${commands}" 2>&1 >"/dev/null")" ; then
		if [ "${error}" == "" ] ; then
			error="Command failed: ${commands}"
		fi

		echo "${FUNCNAME[1]}: ${error}" >&2
		exit 1
	fi
}


syncSrc () {
	local file
	local destDir="${here}/src/optimus-manager"

	so mkdir --parents "${destDir}"
	cd "${here}/.."

	while read -r file; do
		rsync --archive "${file}" "${destDir}"
	done < <(
		find . -mindepth 1 -maxdepth 1 -not -name "package" -and -not -name ".*" |
		cut --delimiter='/' --fields=2-
	)
}


checkRequiredSoftware
mainFunction
