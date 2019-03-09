---
name: Bug report
about: Report a bug
title: ''
labels: ''
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**System info**
Please include :
- Your distribution
- Your desktop manager (KDE, GNOME, Cinnamon...), if you have one
- You display manager (SDDM, GDM, LightDM...), if you have one. If you do not know, you are probably using the one coming with your desktop manager.
- Your laptop model, if you think it could be related to the problem


**Logs**
Please attach the following logs (if you are able to):
- Kernel (if you think the problem could be driver-related) : if you are still able access to a console after the bug occurs, save the output of the command `dmesg` and post it here.
- Xorg : post the log of `/var/log/Xorg.0.log` (it may be a different number, and there may be multiple logs, In that case post them all). This log is only created *after* the X server stops, so you may have to reboot your computer or restart the display manager after the bug occurs.
- Display manager : save and post the output of `journalctl -u <service name> -b0 --no-pager`. Replace `<service name>` by the name of the display manager service (see the Troubleshooting section of the README). If you have rebooted once since the bug occurred, replace `-b0` with `-b-1`.
- Daemon : same instructions with `optimus-manager` instead.

*Do not directly copy paste the logs into the GitHub issue.* Save them to pastebins (https://pastebin.com/) and post the links here.
