#!/bin/bash
# Copy videos from a USB stick to the TV.
#
# Started by udev through tvautocopy@<device>.service whenever a USB storage
# device with a filesystem is plugged in. Mounts it, mirrors the "simpsonstv"
# folder into the videos folder, unmounts it. The LED is lit while copying.
#
# NOTE: this is a mirror (rsync --delete-before). Videos on the TV that are not
# in the stick's simpsonstv folder are deleted.
#
# Usage: autocopy.sh <device name, e.g. sda1>

set -u

DEVICE_NAME="${1:?usage: autocopy.sh <device name, e.g. sda1>}"
DEVICE="/dev/${DEVICE_NAME}"
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
DEST_DIR="${SIMPSONSTV_VIDEO_DIR:-${SCRIPT_DIR}/videos}"
USB_FOLDER="simpsonstv"
LED_PIN="${AUTOCOPY_LED_PIN:-27}"
LOG_FILE_NAME="simpsontv_log.txt"
MOUNT_POINT="/run/simpsonstv/usb-${DEVICE_NAME}"

led() { pinctrl set "${LED_PIN}" op "$1"; }   # dh = on, dl = off

cleanup() {
        sync
        if mountpoint -q "${MOUNT_POINT}"; then
                umount "${MOUNT_POINT}"
        fi
        rmdir "${MOUNT_POINT}" 2>/dev/null
        led dl
}

mkdir -p "${MOUNT_POINT}"
trap cleanup EXIT

if ! mount "${DEVICE}" "${MOUNT_POINT}"; then
        echo "Could not mount ${DEVICE}"
        exit 1
fi

if [ ! -d "${MOUNT_POINT}/${USB_FOLDER}" ]; then
        echo "No ${USB_FOLDER} folder on ${DEVICE}, nothing to copy"
        exit 0
fi

led dh
mkdir -p "${DEST_DIR}"
owner="$(stat -c '%U:%G' "${DEST_DIR}")"

echo "Copying ${DEVICE}/${USB_FOLDER}/ to ${DEST_DIR}/"
rsync -rtvh --delete-before --exclude=encode.py \
        "${MOUNT_POINT}/${USB_FOLDER}/" "${DEST_DIR}/" \
        > "${MOUNT_POINT}/${LOG_FILE_NAME}" 2>&1
status=$?

# Files were copied as root; give them back to whoever owns the videos folder.
chown -R "${owner}" "${DEST_DIR}"

if [ ${status} -eq 0 ]; then
        echo "Copy finished"
else
        echo "rsync failed with status ${status}, see ${LOG_FILE_NAME} on the stick"
fi
exit ${status}
