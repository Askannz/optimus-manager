import os
import optimus_manager.envs as envs


def clean_xorg():

    try:
        os.remove(envs.XORG_CONF_PATH)
        print("Removed %s" % envs.XORG_CONF_PATH)
    except FileNotFoundError:
        pass


def clean_login_managers():

    def _clean_sddm():

        CONF_FOLDER_PATH = "/etc/sddm.conf.d/"
        conf_filepath = os.path.join(CONF_FOLDER_PATH, envs.SDDM_CONF_NAME)

        try:
            os.remove(conf_filepath)
            print("Removed %s" % conf_filepath)
        except FileNotFoundError:
            pass

    def _clean_lightdm():

        CONF_FOLDER_PATH = "/etc/lightdm.conf.d/"
        conf_filepath = os.path.join(CONF_FOLDER_PATH, envs.LIGHTDM_CONF_NAME)

        try:
            os.remove(conf_filepath)
            print("Removed %s" % conf_filepath)
        except FileNotFoundError:
            pass

    def _clean_gdm():

        FOLDER_1_PATH = "/usr/share/gdm/greeter/autostart/"
        FOLDER_2_PATH = "/etc/xdg/autostart/"

        file_1_path = os.path.join(FOLDER_1_PATH, envs.GDM_DESKTOP_FILE_NAME)
        file_2_path = os.path.join(FOLDER_2_PATH, envs.GDM_DESKTOP_FILE_NAME)

        try:
            os.remove(file_1_path)
            print("Removed %s" % file_1_path)
        except FileNotFoundError:
            pass

        try:
            os.remove(file_2_path)
            print("Removed %s" % file_2_path)
        except FileNotFoundError:
            pass

    # -----------

    _clean_sddm()
    _clean_lightdm()
    _clean_gdm()
