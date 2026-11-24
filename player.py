"""Play every video in the videos folder in random order, forever."""
import random
import time

import mpvctl


def main():
    mpvctl.ensure_run_dir()
    while True:
        # Re-read the folder each pass so videos copied from USB get picked up.
        videos = mpvctl.list_videos()
        if not videos:
            print('No videos found in ' + mpvctl.VIDEO_DIR)
            time.sleep(5)
            continue
        random.shuffle(videos)
        for video in videos:
            print('Current video: ' + video)
            mpvctl.play(video)


if __name__ == '__main__':
    main()
