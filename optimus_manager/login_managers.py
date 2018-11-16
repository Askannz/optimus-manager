import os
import time
import optimus_manager.envs as envs
from optimus_manager.detection import get_login_managers
import optimus_manager.checks as checks
from optimus_manager.bash import exec_bash


class LoginManagerError(Exception):
    pass


def stop_login_manager(config):

    login_manager_service_name = config["optimus"]["login_manager"]

    if login_manager_service_name == "":
        return

    if checks.is_login_manager_active(config):

        exec_bash("systemctl stop %s" % login_manager_service_name)

        if checks.is_login_manager_active(config):
            print("Warning : cannot stop service %s. Continuing..." % login_manager_service_name)
        else:
            stopped = _wait_xorg_stop()
            if not stopped:
                print("Warning : Xorg server does not want to stop. Continuing...")


def restart_login_manager(config):

    login_manager_service_name = config["optimus"]["login_manager"]

    if login_manager_service_name == "":
        return

    exec_bash("systemctl restart %s" % login_manager_service_name)

    if not checks.is_login_manager_active(config):
        print("Warning : cannot restart service %s. Continuing..." % login_manager_service_name)


def configure_login_managers(mode):

    login_managers = get_login_managers()

    if len(login_managers) == 0:
        msg = "No supported login manager detected. Please manually configure" \
              "your login manager to use the display setup script at %s. If you" \
              "use xinit, add this script to your .xinitrc" % envs.XSETUP_PATH
        print(msg)
        return

    for manager_name in login_managers:

        if manager_name == "sddm":
            _configure_sddm(mode)
        elif manager_name == "lightdm":
            _configure_lightdm(mode)
        elif manager_name == "gdm":
            _configure_gdm(mode)


def _configure_sddm(mode):

    CONF_FOLDER_PATH = "/etc/sddm.conf.d/"

    conf_filepath = os.path.join(CONF_FOLDER_PATH, envs.SDDM_CONF_NAME)

    if mode == "intel":

        if os.path.isfile(conf_filepath):
            os.remove(conf_filepath)

    elif mode == "nvidia":

        if not os.path.isdir(CONF_FOLDER_PATH):
            os.mkdir(CONF_FOLDER_PATH)

        text = "[X11]\n" \
               "DisplayCommand=%s\n" % envs.XSETUP_PATH

        try:
            with open(conf_filepath, 'w') as f:
                f.write(text)

        except IOError:
            raise LoginManagerError("Cannot write to %s" % conf_filepath)


def _configure_lightdm(mode):

    CONF_FOLDER_PATH = "/etc/lightdm.conf.d/"

    conf_filepath = os.path.join(CONF_FOLDER_PATH, envs.LIGHTDM_CONF_NAME)

    if mode == "intel":

        if os.path.isfile(conf_filepath):
            os.remove(conf_filepath)

    elif mode == "nvidia":

        if not os.path.isdir(CONF_FOLDER_PATH):
            os.mkdir(CONF_FOLDER_PATH)

        text = "[Seat:*]\n" \
               "display-setup-script=%s\n" % envs.XSETUP_PATH

        try:
            with open(conf_filepath, 'w') as f:
                f.write(text)

        except IOError:
            raise LoginManagerError("Cannot write to %s" % conf_filepath)


def _configure_gdm(mode):

    FOLDER_1_PATH = "/usr/share/gdm/greeter/autostart/"
    FOLDER_2_PATH = "/etc/xdg/autostart/"

    file_1_path = os.path.join(FOLDER_1_PATH, envs.GDM_DESKTOP_FILE_NAME)
    file_2_path = os.path.join(FOLDER_1_PATH, envs.GDM_DESKTOP_FILE_NAME)

    if mode == "intel":

        if os.path.isfile(file_1_path):
            os.remove(file_1_path)

        if os.path.isfile(file_2_path):
            os.remove(file_2_path)

    elif mode == "nvidia":

        if not os.path.isdir(FOLDER_1_PATH):
            os.makedirs(FOLDER_1_PATH)

        if not os.path.isdir(FOLDER_2_PATH):
            os.makedirs(FOLDER_2_PATH)

        text = "[Desktop Entry]\n" \
               "Type=Application\n" \
               "Name=Optimus Manager X Setup\n" \
               "Exec=sh -c \"xrandr --setprovideroutputsource modesetting NVIDIA-0; xrandr --auto\"\n" \
               "NoDisplay=true\n" \
               "X-GNOME-Autostart-Phase=DisplayServer\n"

        try:

            for filepath in [file_1_path, file_2_path]:
                with open(filepath, 'w') as f:
                    f.write(text)

        except IOError:
            raise LoginManagerError("Cannot write to %s" % filepath)


def _wait_xorg_stop():

    POLL_TIME = 0.5
    TIMEOUT = 10.0

    t0 = time.time()
    t = t0
    while abs(t-t0) < TIMEOUT:
        if not checks.is_xorg_running():
            return True
        else:
            time.sleep(POLL_TIME)
            t = time.time()

    return False
