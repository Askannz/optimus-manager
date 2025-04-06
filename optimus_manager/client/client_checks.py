import sys
from .. import checks
from .. import sessions


def run_switch_checks(config, requested_mode):
    _check_daemon_active()
    _check_bbswitch_module(config)
    _check_nvidia_module(requested_mode)
    _check_patched_GDM()
    _check_number_of_sessions()


def _check_bbswitch_module(config):
    if config["optimus"]["switching"] == "bbswitch" and not checks.is_module_available("bbswitch"):
        print("Not properly installed: bbswitch")
        sys.exit(1)


def _check_daemon_active():
    if not checks.is_daemon_active():
        print("Not started: optimus-manager.service")
        sys.exit(1)


def _check_number_of_sessions():
    nb_desktop_sessions = sessions.get_number_of_desktop_sessions(ignore_gdm=True)

    if nb_desktop_sessions > 1:
        print("Unable to switch: Other users are logged in")
        sys.exit(1)


def _check_nvidia_module(requested_mode):
    if requested_mode == "nvidia" and not checks.is_module_available("nvidia"):
        print("Not properly installed: nvidia")
        sys.exit(1)


def _check_patched_GDM():
    try:
        dm_name = checks.get_current_display_manager()

    except checks.CheckError as error:
        print("Unable to get the display manager name: %s" % str(error))
        return

    if dm_name == "gdm" and not checks.using_patched_GDM():
        print("Not properly installed: gdm-prime")
        sys.exit(1)
