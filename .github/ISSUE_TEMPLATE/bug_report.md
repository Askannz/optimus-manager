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
- The version of optimus-manager you are using : latest stable release (optimus-manager), or the latest Git version (optimus-manager-git)
- Your custom optimus-manager configuration file at `/etc/optimus-manager/optimus-manager.conf`, if you made one

**Logs**
Run `optimus-manager --status` in a console, and if an error message appears, post it here. The message should also point you to a log path, attach it here as well. If there is no error message but you are still experiencing issues, grab the most recent files in `/var/log/optimus-manager/switch/` and `/var/log/optimus-manager/daemon/`.
