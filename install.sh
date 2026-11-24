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
  - install packages: mpv python3-gpiozero python3-lgpio
  - back up and edit ${CONFIG_TXT} (PWM audio on GPIO18/19)
  - back up and edit ${CMDLINE_TXT} (add: ${CMDLINE_ADD})
  - install and enable systemd services tvbutton and tvplayer
    for the code in ${INSTALL_DIR}
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
apt-get install -y mpv python3-gpiozero python3-lgpio
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
mkdir -p "${INSTALL_DIR}/videos"
chown "${owner}:" "${INSTALL_DIR}/videos"

echo "== Services"
for unit in tvbutton.service tvplayer.service; do
        sed "s|@INSTALL_DIR@|${INSTALL_DIR}|g" "${INSTALL_DIR}/services/${unit}" \
                > "/etc/systemd/system/${unit}"
        echo "   installed /etc/systemd/system/${unit}"
done

# USB autocopy was removed; clean up what an earlier version of this script installed.
for old in /etc/udev/rules.d/99-simpsonstv-autocopy.rules /etc/systemd/system/tvautocopy@.service; do
        if [ -e "${old}" ]; then
                rm -f "${old}"
                echo "   removed old ${old}"
        fi
done

systemctl daemon-reload
udevadm control --reload
systemctl enable tvbutton.service tvplayer.service

echo
echo "Done. Reboot to apply the boot changes: sudo reboot"
