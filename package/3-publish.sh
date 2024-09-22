#! /bin/bash
set -e

here="$(realpath "$(dirname "${0}")")"
files=("optimus-manager.install" "PKGBUILD")


mainFunction () {
	#checkUncommittedChanges
	cloneAurRepo
	checkFilesHaveBeenChanged
	syncFiles
	updateSrcinfo
	uploadChanges
	removeAurRepoClone
}


checkFilesHaveBeenChanged () {
	local aurSum
	local changed=false
	local file
	local index=0
	local repoSum

	while [[ "${index}" -lt "${#files[@]}" ]] && ! "${changed}"; do
		repoSum="$(fileSum "${here}/${files[$index]}")"
		aurSum="$(fileSum "${here}/optimus-manager-git/${files[$index]}")"

		if [[ "${repoSum}" != "${aurSum}" ]]; then
			changed=true
		else
			index="$((index +1))"
		fi
	done

	if ! "${changed}"; then
		removeAurRepoClone
		exit 0
	fi
}


checkUncommittedChanges () {
	local uncommittedChanges; uncommittedChanges="$(uncommittedChanges)"

	if [[ -n "${uncommittedChanges}" ]]; then
		echo "Cannot publish: Uncommitted changes:" >&2
		echo "${uncommittedChanges}" >&2
		exit 1
	fi
}


cloneAurRepo () {
	cd "${here}"

	if [[ ! -d "optimus-manager-git" ]]; then
		so git clone \
			--depth 1 --shallow-submodules \
			"ssh://aur@aur.archlinux.org/optimus-manager-git.git"
	else
		so git fetch
	fi
}


fileLastCommitDescription () {
	local file="${1}"

	cd "${here}"
	git log -1 --pretty=format:%s -- "${file}"
}


fileModificationEpoch () {
	local file="${1}"
	stat --format=%Y "${file}"
}


fileSum () {
	local file="${1}"

	sha1sum "${file}" |
	cut --delimiter=' ' --fields=1
}


lastUpdatedFile () {
	local epoch=0
	local file
	local oldEpoch
	local result

	for file in "${files[@]}"; do
		oldEpoch="${epoch}"
		epoch="$(fileModificationEpoch "${here}/${file}")"

		if [[ "${epoch}" -gt "${oldEpoch}" ]]; then
			result="${file}"
		fi
	done

	echo "${result}"
}


removeAurRepoClone () {
	so rm --recursive --force "${here}/optimus-manager-git"
}


so () {
	local error

	if ! error="$(${@} 2>&1 >"/dev/null")" ; then
		if [[ -z "${error}" ]] ; then
			error="Command failed"
		fi

		echo "${FUNCNAME[1]}: ${*}:" >&2
		echo "${error}" >&2
		exit 1
	fi
}


syncFiles () {
	local file

	for file in "${files[@]}"; do
		so cp --force "${here}/${file}" "${here}/optimus-manager-git/${file}"
	done
}


uncommittedChanges () {
	cd "${here}"
	git status --porcelain
}


updateSrcinfo () {
	cd "${here}/optimus-manager-git"
	makepkg --printsrcinfo > .SRCINFO
}


uploadChanges () {
	cd "${here}/optimus-manager-git"

	local description; description="$(fileLastCommitDescription "$(lastUpdatedFile)")"
	if [[ -z "${description}" ]]; then
		echo "${FUNCNAME[0]}: Unable to upload: Empty description" >&2
		exit 1
	fi

	echo "${description}"
	echo so git add --all
	echo so git commit --message="${description}"
}


mainFunction
