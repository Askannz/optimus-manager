from .. import envs
from ..checks import get_active_renderer, check_offloading_available


def report_errors(state):

    if state is None:
        print("ERROR: no state file found. Is optimus-manager.service running ?")
        return True

    elif state["type"] == "startup_failed":
        print("ERROR: the optimus-manager service failed boot-time startup.")
        print("Log at %s/daemon/daemon-%s.log" % (envs.LOG_DIR_PATH, state["daemon_run_id"]))
        return True

    elif state["type"] == "pending_pre_xorg_start":
        if state["current_mode"] is None:
            print("ERROR: a GPU setup was initiated but Xorg pre-start hook did not run.")
            print("Log at %s/switch/switch-%s.log" % (envs.LOG_DIR_PATH, state["switch_id"]))
            return True
        else:
            print("A GPU switch from %s to %s is pending." % (state["current_mode"], state["requested_mode"]))
            print("Log out and log back in to apply.")

    elif state["type"] == "pre_xorg_start_failed":
        print("ERROR: the latest GPU setup attempt failed at Xorg pre-start hook.")
        print("Log at %s/switch/switch-%s.log" % (envs.LOG_DIR_PATH, state["switch_id"]))
        return True

    elif state["type"] == "pending_post_xorg_start":
        print("ERROR: a GPU setup was initiated but Xorg post-start hook did not run.")
        print("Log at %s/switch/switch-%s.log" % (envs.LOG_DIR_PATH, state["switch_id"]))
        print("If your login manager is GDM, make sure to follow those instructions:")
        print("https://github.com/Askannz/optimus-manager#important--gnome-and-gdm-users")
        print("If your display manager is neither GDM, SDDM nor LightDM, or if you don't use one, read the wiki:")
        print("https://github.com/Askannz/optimus-manager/wiki/FAQ,-common-issues,-troubleshooting")
        return True

    elif state["type"] == "post_xorg_start_failed":
        print("ERROR: the latest GPU setup attempt failed at Xorg post-start hook.")
        print("Log at %s/switch/switch-%s.log" % (envs.LOG_DIR_PATH, state["switch_id"]))
        return True

    elif state["type"] == "done":

        expected_renderer = {
            "intel": "intel",
            "hybrid": "intel",
            "nvidia": "nvidia"
        }[state["current_mode"]]

        active_renderer = get_active_renderer()

        if expected_renderer != active_renderer:
            print("ERROR: the active card is \"%s\" but it should be \"%s\"." % (expected_renderer, active_renderer))
            print("Something went wrong during the last GPU setup...")
            print("Log at %s/switch/switch-%s.log" % (envs.LOG_DIR_PATH, state["switch_id"]))
            return True

        if state["current_mode"] == "hybrid" and not check_offloading_available():
            print("WARNING: hybrid mode is set but Nvidia card does not seem to be available for offloading.")
            print("Log at %s/switch/switch-%s.log" % (envs.LOG_DIR_PATH, state["switch_id"]))

        return False

    else:
        assert False
