#! /bin/bash
set -e

#  for executing this, in the terminal application enter:
#  curl -s https://raw.githubusercontent.com/Askannz/optimus-manager/master/package/install.sh | bash


mainFunction () {
	cd "${HOME}"
	cloneRepo
	cd optimus-manager/package
	makePackage
	installPackage
}


cleanUp () {
	cd "${HOME}"
	rm --recursive --force "optimus-manager"
}


cloneRepo () {
	git clone --depth 1 --shallow-submodules https://github.com/Askannz/optimus-manager
}


installPackage () {
	sudo pacman --upgrade ./*.pkg.*
}


prepareEnvironment () {
	sudo -v
	trap 'cleanUp' INT TERM QUIT ERR EXIT
}


makePackage () {
	PACKAGER="${USER} <@${HOSTNAME}>" makepkg --syncdeps --needed --rmdeps --skippgpcheck --force --noconfirm
}


prepareEnvironment
mainFunction
