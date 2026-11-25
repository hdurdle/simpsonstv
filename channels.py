"""TV channels with a live, real-time schedule.

Each top-level folder in videos/ is a channel. A channel plays its episodes in
order and loops, on a schedule worked out from the clock, so it keeps "airing"
while you watch something else. Tuning in joins whatever is on now, part-way
through. Episode files loose in videos/ itself form one extra channel.
"""
import bisect
import hashlib
import json
import os
import re
import subprocess
import time

LOOSE_FILES_CHANNEL = 'Mixed'
# Files changed more recently than this are probably still uploading; skip them.
MIN_AGE_SECONDS = 60


def natural_key(text):
    """Sort key that puts 'Episode 2' before 'Episode 10'."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r'(\d+)', text)]


def probe_duration(path):
    """Length of a video in seconds, or None if it can't be read (yet)."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', path],
            capture_output=True, text=True, timeout=60)
        duration = float(result.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return duration if duration > 1 else None


class DurationCache:
    """Episode lengths, saved to disk so each file is only probed once."""

    def __init__(self, path, probe=probe_duration):
        self.path = path
        self.probe = probe
        self.dirty = False
        try:
            with open(path) as file:
                self.entries = json.load(file)
        except (OSError, ValueError):
            self.entries = {}

    def duration(self, path, stat):
        signature = [stat.st_size, int(stat.st_mtime)]
        entry = self.entries.get(path)
        if entry and entry[:2] == signature:
            return entry[2]
        duration = self.probe(path)
        if duration is None:
            return None  # not cached, so it's tried again on the next scan
        self.entries[path] = signature + [duration]
        self.dirty = True
        return duration

    def keep_only(self, paths):
        for path in list(self.entries):
            if path not in paths:
                del self.entries[path]
                self.dirty = True

    def save(self):
        if not self.dirty:
            return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        temporary = self.path + '.tmp'
        with open(temporary, 'w') as file:
            json.dump(self.entries, file)
        os.replace(temporary, self.path)
        self.dirty = False


class Channel:
    def __init__(self, name, episodes):
        """episodes: list of (path, duration in seconds), in airing order."""
        self.name = name
        self.paths = [path for path, _ in episodes]
        self.starts = []
        total = 0.0
        for _, duration in episodes:
            self.starts.append(total)
            total += duration
        self.length = total
        # Start each channel at a different point in its loop, so channels
        # don't all change episode at the same moment.
        digest = int(hashlib.md5(name.encode('utf-8')).hexdigest(), 16)
        self.stagger = digest % max(1, int(self.length))

    def on_air(self, now):
        """(episode path, seconds into it) that this channel is showing at time `now`."""
        return self.upcoming(now, 1)[0]

    def upcoming(self, now, count=2):
        """What's on at `now` and the episodes after it, as a list of
        (path, seconds to start at): the first part-way through, the rest from
        the beginning (None)."""
        position = (now + self.stagger) % self.length
        index = bisect.bisect_right(self.starts, position) - 1
        items = [(self.paths[index], position - self.starts[index])]
        for step in range(1, count):
            items.append((self.paths[(index + step) % len(self.paths)], None))
        return items

    def __repr__(self):
        return 'Channel(%r, %d episodes, %.0f min loop)' % (self.name, len(self.paths), self.length / 60)


def scan(video_dir, cache, now=None):
    """Build the channel line-up from the video folder, sorted by channel name."""
    now = time.time() if now is None else now
    groups = {}
    seen = set()
    for folder, subfolders, files in os.walk(video_dir):
        subfolders[:] = [name for name in subfolders if not name.startswith('.')]
        relative = os.path.relpath(folder, video_dir)
        channel_name = LOOSE_FILES_CHANNEL if relative == '.' else relative.split(os.sep)[0]
        for name in files:
            if name.startswith('.') or not name.lower().endswith('.mp4'):
                continue
            path = os.path.join(folder, name)
            try:
                stat = os.stat(path)
            except OSError:
                continue
            if now - stat.st_mtime < MIN_AGE_SECONDS:
                continue
            seen.add(path)
            duration = cache.duration(path, stat)
            if duration:
                groups.setdefault(channel_name, []).append((path, duration))
    cache.keep_only(seen)
    cache.save()

    lineup = []
    for name in sorted(groups, key=natural_key):
        episodes = sorted(groups[name], key=lambda item: natural_key(os.path.relpath(item[0], video_dir)))
        lineup.append(Channel(name, episodes))
    return lineup
