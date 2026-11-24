"""Play the videos in name order and remember the current one across reboots."""
import os
import time

import mpvctl

LAST_PLAYED_FILE = os.path.join(mpvctl.BASE_DIR, 'LastPlayed.txt')


def save_last_played(video):
    with open(LAST_PLAYED_FILE, 'w') as file:
        file.write(video)


def get_last_played():
    if not os.path.exists(LAST_PLAYED_FILE):
        return ''
    with open(LAST_PLAYED_FILE) as file:
        return file.read().strip()


def main():
    mpvctl.ensure_run_dir()
    while True:
        videos = mpvctl.list_videos()
        if not videos:
            print('No videos found in ' + mpvctl.VIDEO_DIR)
            time.sleep(5)
            continue
        last_played = get_last_played()
        start_index = videos.index(last_played) if last_played in videos else 0
        for video in videos[start_index:]:
            save_last_played(video)
            print('Current video: ' + video)
            mpvctl.play(video)
        # Reached the end of the list: start again from the first video.
        save_last_played('')


if __name__ == '__main__':
    main()
