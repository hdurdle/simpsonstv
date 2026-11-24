#!/bin/bash
# Simpsons TV installer for Raspberry Pi OS Lite (Bookworm or newer) on a Pi Zero 2 W.
#
# Run from the cloned repo:  sudo ./install.sh        (add -y to skip the prompt)
# Safe to run again: boot-file edits are only made once, and the original
# boot files are backed up next to themselves before the first change.

set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
BOOT_DIR="/boot/firmware"
CONFIG_TXT="${BOOT_DIR}/config.txt"
CMDLINE_TXT="${BOOT_DIR}/cmdline.txt"
MARKER_BEGIN="# >>> simpsonstv >>>"
MARKER_END="# <<< simpsonstv <<<"
# Force the Waveshare 4" panel (480x800 portrait, rotated by mpv) and keep the
# text console off the screen so it doesn't flash between videos.
CMDLINE_ADD="video=HDMI-A-1:480x800M@60D fbcon=map:10"
SMB_CONF="/etc/samba/smb.conf"

if [ "$(id -u)" -ne 0 ]; then
        echo "Please run with sudo: sudo ./install.sh" >&2
        exit 1
fi
if [ ! -f "${CONFIG_TXT}" ] || [ ! -f "${CMDLINE_TXT}" ]; then
        echo "${CONFIG_TXT} not found. This installer needs Raspberry Pi OS Bookworm or newer." >&2
        exit 1
fi

owner="$(stat -c '%U' "${INSTALL_DIR}")"

cat <<EOF
This will:
  - install packages: mpv ffmpeg python3-gpiozero python3-lgpio samba
  - back up and edit ${CONFIG_TXT} (PWM audio on GPIO18/19)
  - back up and edit ${CMDLINE_TXT} (add: ${CMDLINE_ADD})
  - install and enable the systemd service simpsonstv
    for the code in ${INSTALL_DIR}
  - back up and edit ${SMB_CONF}: add a network share "videos" for
    ${INSTALL_DIR}/videos with NO PASSWORD. Anyone on your local network
    can add, change and delete episodes.
EOF
if [ "${1:-}" != "-y" ]; then
        read -r -p "Continue? [y/N] " answer
        case "${answer}" in
                [yY]*) ;;
                *) echo "Cancelled."; exit 1 ;;
        esac
fi

echo "== Installing packages"
apt-get update
# ffmpeg provides ffprobe, used to read episode lengths for the schedule
apt-get install -y mpv ffmpeg python3-gpiozero python3-lgpio
DEBIAN_FRONTEND=noninteractive apt-get install -y samba
if ! command -v pinctrl >/dev/null; then
        apt-get install -y raspi-utils
fi

backup() {
        local file="$1"
        local copy
        copy="${file}.simpsonstv-$(date +%Y%m%d-%H%M%S).bak"
        cp -a "${file}" "${copy}"
        echo "   backed up ${file} to ${copy}"
}

echo "== Boot configuration"
if grep -qF "${MARKER_BEGIN}" "${CONFIG_TXT}"; then
        echo "   ${CONFIG_TXT} already configured, skipping"
else
        backup "${CONFIG_TXT}"
        cat >> "${CONFIG_TXT}" <<EOF

${MARKER_BEGIN}
[all]
# PWM audio out on GPIO18/19; the amplifier is on GPIO19
dtparam=audio=on
dtoverlay=audremap,pins_18_19
${MARKER_END}
EOF
        echo "   updated ${CONFIG_TXT}"
fi

if grep -qF "video=HDMI-A-1:" "${CMDLINE_TXT}"; then
        echo "   ${CMDLINE_TXT} already has a video= setting, skipping"
else
        backup "${CMDLINE_TXT}"
        # cmdline.txt must stay a single line
        sed -i "1 s|\$| ${CMDLINE_ADD}|" "${CMDLINE_TXT}"
        echo "   updated ${CMDLINE_TXT}"
fi

echo "== Settings"
if [ -f "${INSTALL_DIR}/simpsonstv.conf" ]; then
        echo "   ${INSTALL_DIR}/simpsonstv.conf exists, leaving it alone"
else
        cp "${INSTALL_DIR}/simpsonstv.conf.example" "${INSTALL_DIR}/simpsonstv.conf"
        chown "${owner}:" "${INSTALL_DIR}/simpsonstv.conf"
        echo "   created ${INSTALL_DIR}/simpsonstv.conf"
fi
mkdir -p "${INSTALL_DIR}/videos" "${INSTALL_DIR}/cache"
chown "${owner}:" "${INSTALL_DIR}/videos" "${INSTALL_DIR}/cache"

echo "== Services"
# Clean up what earlier versions of this script installed: the separate
# player and button services (now one simpsonstv service) and USB autocopy.
for old in tvplayer.service tvbutton.service; do
        if [ -e "/etc/systemd/system/${old}" ]; then
                systemctl disable --now "${old}" || true
                rm -f "/etc/systemd/system/${old}"
                echo "   removed old ${old}"
        fi
done
for old in /etc/udev/rules.d/99-simpsonstv-autocopy.rules /etc/systemd/system/tvautocopy@.service; do
        if [ -e "${old}" ]; then
                rm -f "${old}"
                echo "   removed old ${old}"
        fi
done

sed "s|@INSTALL_DIR@|${INSTALL_DIR}|g" "${INSTALL_DIR}/services/simpsonstv.service" \
        > /etc/systemd/system/simpsonstv.service
echo "   installed /etc/systemd/system/simpsonstv.service"

systemctl daemon-reload
udevadm control --reload
systemctl enable simpsonstv.service

echo "== Network share"
# Open guest share for uploading episodes, one folder per show. Files are
# written as ${owner} so the player can read them and you can manage them over ssh.
group="$(id -gn "${owner}")"
backup "${SMB_CONF}"
smb_backup="$(ls -t "${SMB_CONF}".simpsonstv-*.bak | head -1)"
# Replace our block if an earlier run added it
sed -i "/^${MARKER_BEGIN}\$/,/^${MARKER_END}\$/d" "${SMB_CONF}"
# Guests need "map to guest = bad user" in [global] (Debian's default, but make sure)
if [ "$(testparm -s --parameter-name='map to guest' 2>/dev/null)" != "Bad User" ]; then
        sed -i '/^\[global\]/a \   map to guest = bad user' "${SMB_CONF}"
fi
cat >> "${SMB_CONF}" <<EOF
${MARKER_BEGIN}
# Simpsons TV: upload episodes here, one folder per show.
# No password: anyone on the local network can add, change and delete files.
[videos]
   comment = Simpsons TV episodes (one folder per show)
   path = ${INSTALL_DIR}/videos
   browseable = yes
   read only = no
   guest ok = yes
   guest only = yes
   force user = ${owner}
   force group = ${group}
   create mask = 0664
   directory mask = 0775
   # local networks only, never the internet
   hosts allow = 127.0.0.1 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 169.254.0.0/16 ::1 fe80::/10 fc00::/7
   # hide Mac/Windows clutter and the encoder script
   veto files = /._*/.DS_Store/Thumbs.db/desktop.ini/encode.py/
   delete veto files = yes
${MARKER_END}
EOF
if testparm -s >/dev/null 2>&1; then
        systemctl enable --now smbd
        systemctl restart smbd
        echo "   share ready: \\\\$(hostname).local\\videos  (smb://$(hostname).local/videos)"
else
        cp -a "${smb_backup}" "${SMB_CONF}"
        echo "   Samba rejected the new settings; restored ${SMB_CONF} from ${smb_backup}." >&2
        echo "   Run 'testparm -s' to see the error." >&2
        exit 1
fi

echo
echo "Done. Reboot to apply the boot changes: sudo reboot"
