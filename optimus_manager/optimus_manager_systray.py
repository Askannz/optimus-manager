import argparse
import socket
import sys
import signal
import traceback
from functools import partial

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QWidget, QMessageBox, QErrorMessage
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
import optimus_manager.checks as checks
import optimus_manager.envs as envs

NVIDIA = 'nvidia'
INTEL = 'intel'

NVIDIA_ICON = QIcon.fromTheme('nvidia', QIcon('../icon/nvidia.svg'))
INTEL_ICON = QIcon.fromTheme('intel', QIcon('../icon/intel.svg'))


# Next 3 funcs courtesy of https://coldfix.eu/2016/11/08/pyqt-boilerplate

def setup_interrupt_handling():
    """Setup handling of KeyboardInterrupt (Ctrl-C) for PyQt."""
    signal.signal(signal.SIGINT, _interrupt_handler)
    # Regularly run some (any) python code, so the signal handler gets a
    # chance to be executed:
    safe_timer(50, lambda: None)


def _interrupt_handler(signum, frame):
    """Handle KeyboardInterrupt: quit application."""
    QApplication.quit()


def safe_timer(timeout, func, *args, **kwargs):
    """
    Create a timer that is safe against garbage collection and overlapping
    calls. See: http://ralsina.me/weblog/posts/BB974.html
    """

    def timer_event():
        try:
            func(*args, **kwargs)
        finally:
            QTimer.singleShot(timeout, timer_event)

    QTimer.singleShot(timeout, timer_event)


def send_command(cmd, parent=None):
    """Send a command to daemon."""
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        client.connect(envs.SOCKET_PATH)
        client.send(cmd.encode('utf-8'))
        client.close()

    except (ConnectionRefusedError, OSError):
        msg = ("Cannot connect to the UNIX socket at %s. Is optimus-manager-daemon running?\n"
               "You can enable and start it by running these commands as root:\n"
               "systemctl enable optimus-manager.service\n"
               "systemctl start optimus-manager.service" % envs.SOCKET_PATH)
        print(msg)
        error_dialog = QErrorMessage(parent)
        error_dialog.showMessage(msg)


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, mode, parent=None):
        self.parent = parent
        QSystemTrayIcon.__init__(self, NVIDIA_ICON if mode == NVIDIA else INTEL_ICON, self.parent)
        menu = QMenu(self.parent)

        # Nvidia menu item bound to self.switch('nvidia')
        nvidia_action = menu.addAction(NVIDIA_ICON, "Switch to nvidia" if mode == INTEL else "Reload nvidia")
        nvidia_action.triggered.connect(partial(self.switch, NVIDIA))

        # Intel menu item bound to self.switch('intel')
        intel_action = menu.addAction(INTEL_ICON, "Switch to intel" if mode == NVIDIA else "Reload intel")
        intel_action.triggered.connect(partial(self.switch, INTEL))

        # Provide an easy menu item to close the "app"
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.exit)

        # Set the menu and proper tooltip
        self.setContextMenu(menu)
        self.setToolTip('optimus-manager ({mode})'.format(mode=mode))

    def exit(self):
        """Exit gracefully."""
        QApplication.exit()

    def confirm(self, to):
        """Ask if user is sure they want to switch GPU."""
        msg = QMessageBox(self.parent)

        # Make a pixmap out of the proper icon and use it as the icon
        msg.setIconPixmap((NVIDIA_ICON if to == NVIDIA else INTEL_ICON).pixmap(64, 64))

        msg.setWindowTitle('WARNING: You are about to switch GPUs')
        msg.setText("You are about to switch to the {to} GPU. "
                    "This will restart the display manager and all your applications WILL CLOSE.\n"
                    "Would you like to continue?".format(to=to))

        yes = msg.addButton('Yes, switch GPU', QMessageBox.AcceptRole)
        no = msg.addButton('No, cancel switch', QMessageBox.RejectRole)
        msg.setDefaultButton(no)
        msg.exec()
        if msg.clickedButton() is yes:
            return True
        return False

    def switch(self, to):
        """Switch to a GPU after confirming."""
        print('Confirming switch to', to)
        if self.confirm(to):
            print('Switching')
            send_command(to, self.parent)
        print('Cancelled')


def main():
    # Arguments parsing
    parser = argparse.ArgumentParser(description="Daemon program for the Optimus Manager tool.\n"
                                                 "https://github.com/Askannz/optimus-manager")
    parser.parse_args()

    print("Optimus Manager (systray) version %s" % envs.VERSION)

    # Setup
    app = QApplication(sys.argv)
    # Make sure it doesn't quit after cancelling a confirm prompt
    app.setQuitOnLastWindowClosed(False)

    # Check current mode
    try:
        mode = checks.read_gpu_mode()
        print('Current mode:', mode)
    except checks.CheckError as e:
        msg = "Error reading mode : %s" % str(e)
        print(msg)
        error_dialog = QErrorMessage()
        error_dialog.showMessage(msg)
        sys.exit(app.exec_())

    # Setup systray
    widget = QWidget()
    tray_icon = SystemTrayIcon(mode, widget)
    tray_icon.show()

    # Make sure KeyboardInterrupt signals and exceptions are handled correctly
    setup_interrupt_handling()
    sys.excepthook = traceback.print_exception

    # Start
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
