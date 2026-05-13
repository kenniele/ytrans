#!/usr/bin/env python3
import argparse
import os
import re
import sys

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
)


def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:youtube\.com/watch\?.*?v=)([\w-]{11})',
        r'(?:youtu\.be/)([\w-]{11})',
        r'(?:youtube\.com/embed/)([\w-]{11})',
        r'(?:youtube\.com/shorts/)([\w-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Invalid YouTube URL: {url}")


def is_channel_url(url: str) -> bool:
    return bool(re.search(r'youtube\.com/(@[\w.-]+|channel/[\w-]+|c/[\w-]+)', url))


def fetch_channel_top_videos(url: str, limit: int) -> list[str]:
    """Fetch top N most popular video IDs from a channel using yt-dlp."""
    import json
    import subprocess

    # Add /videos?sort=p to get sorted by popular
    channel_url = re.sub(r'(/videos)?/?(\?.*)?$', '', url)
    channel_url += "/videos?view=0&sort=p"

    cmd = [
        "yt-dlp", "--flat-playlist", "--dump-json",
        "--playlist-items", f"1:{limit}",
        "--no-warnings", "--quiet",
        channel_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "yt-dlp failed to fetch channel")

    ids = []
    for line in result.stdout.strip().split("\n"):
        if line:
            entry = json.loads(line)
            vid = entry.get("id")
            if vid:
                ids.append(vid)
    return ids


def extract_playlist_id(url: str) -> str | None:
    match = re.search(r'[?&]list=([\w-]+)', url)
    return match.group(1) if match else None


def fetch_playlist_video_ids(playlist_id: str) -> list[str]:
    import requests
    resp = requests.get(
        f"https://www.youtube.com/playlist?list={playlist_id}",
        timeout=15,
    )
    ids = re.findall(r'"videoId":"([\w-]{11})"', resp.text)
    seen = set()
    unique = []
    for vid in ids:
        if vid not in seen:
            seen.add(vid)
            unique.append(vid)
    return unique


def fetch_video_title(video_id: str) -> str:
    import requests
    try:
        resp = requests.get(f"https://www.youtube.com/watch?v={video_id}", timeout=10)
        match = re.search(r"<title>(.+?)</title>", resp.text)
        if match:
            title = match.group(1).removesuffix(" - YouTube").strip()
            return title
    except Exception:
        pass
    return video_id


def format_timestamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"[{m:02d}:{s:02d}]"


def transcribe_video(api, video_id, languages, timestamps):
    transcript = api.fetch(video_id, languages=languages)
    title = fetch_video_title(video_id)

    lines = [f"# {title}\n"]
    for snippet in transcript:
        text = snippet.text
        if timestamps:
            text = f"{format_timestamp(snippet.start)} {text}"
        lines.append(text)
    content = "\n".join(lines) + "\n"
    return title, content, transcript.language, transcript.language_code


def save_or_print(content, output_path):
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  → {output_path}", file=sys.stderr)
    else:
        sys.stdout.write(content)


def main():
    parser = argparse.ArgumentParser(description="Extract YouTube video transcript.")
    parser.add_argument("url", help="YouTube video or playlist URL")
    parser.add_argument(
        "--lang", default="ru,en",
        help="Comma-separated language priority list (default: ru,en)",
    )
    parser.add_argument(
        "--timestamps", action="store_true",
        help="Prepend [MM:SS] timestamps to each line",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (single video only)",
    )
    parser.add_argument(
        "-p", "--playlist", action="store_true",
        help="Force treat URL as playlist",
    )
    parser.add_argument(
        "-n", "--top", type=int, default=10,
        help="Number of top videos to fetch from channel (default: 10)",
    )
    args = parser.parse_args()

    languages = [lang.strip() for lang in args.lang.split(",")]
    api = YouTubeTranscriptApi()
    output_dir = os.environ.get("YTRANS_DIR")

    # Determine URL type: channel, playlist, or single video
    playlist_id = extract_playlist_id(args.url)
    is_playlist = args.playlist or (playlist_id is not None)
    is_channel = is_channel_url(args.url)

    # Channel → fetch top N popular videos, then process like a batch
    if is_channel:
        try:
            video_ids = fetch_channel_top_videos(args.url, args.top)
        except Exception as e:
            print(f"Failed to fetch channel: {e}", file=sys.stderr)
            sys.exit(3)

        if not video_ids:
            print("No videos found on channel.", file=sys.stderr)
            sys.exit(1)

        print(f"Channel top {len(video_ids)} videos", file=sys.stderr)
        ok, skip, fail = 0, 0, 0
        total = len(video_ids)

        for i, video_id in enumerate(video_ids, 1):
            output_path = args.output
            if not output_path and output_dir:
                output_path = f"{output_dir}/{video_id}.md"
            if output_path and os.path.exists(output_path):
                print(f"[{i}/{total}] EXISTS {video_id}, skipping", file=sys.stderr)
                skip += 1
                continue

            try:
                title, content, lang, lang_code = transcribe_video(
                    api, video_id, languages, args.timestamps,
                )
                print(f"[{i}/{total}] {title} ({lang_code})", file=sys.stderr)
                save_or_print(content, output_path)
                ok += 1
            except (TranscriptsDisabled, NoTranscriptFound):
                print(f"[{i}/{total}] SKIP {video_id} — no transcript", file=sys.stderr)
                skip += 1
            except Exception as e:
                print(f"[{i}/{total}] FAIL {video_id}", file=sys.stderr)
                fail += 1

        print(f"\nDone: {ok} ok, {skip} skipped, {fail} failed", file=sys.stderr)
        sys.exit(0 if fail == 0 else 2)

    elif is_playlist:
        if not playlist_id:
            print("No playlist ID found in URL.", file=sys.stderr)
            sys.exit(1)

        try:
            video_ids = fetch_playlist_video_ids(playlist_id)
        except Exception as e:
            print(f"Failed to fetch playlist: {e}", file=sys.stderr)
            sys.exit(3)

        if not video_ids:
            print("No videos found in playlist.", file=sys.stderr)
            sys.exit(1)

        print(f"Playlist: {len(video_ids)} videos", file=sys.stderr)
        ok, skip, fail = 0, 0, 0
        total = len(video_ids)

        for i, video_id in enumerate(video_ids, 1):
            output_path = args.output
            if not output_path and output_dir:
                output_path = f"{output_dir}/{video_id}.md"
            if output_path and os.path.exists(output_path):
                print(f"[{i}/{total}] EXISTS {video_id}, skipping", file=sys.stderr)
                skip += 1
                continue

            try:
                title, content, lang, lang_code = transcribe_video(
                    api, video_id, languages, args.timestamps,
                )
                print(f"[{i}/{total}] {title} ({lang_code})", file=sys.stderr)
                save_or_print(content, output_path)
                ok += 1
            except (TranscriptsDisabled, NoTranscriptFound):
                print(f"[{i}/{total}] SKIP {video_id} — no transcript", file=sys.stderr)
                skip += 1
            except Exception as e:
                print(f"[{i}/{total}] FAIL {video_id}", file=sys.stderr)
                fail += 1

        print(f"\nDone: {ok} ok, {skip} skipped, {fail} failed", file=sys.stderr)
        sys.exit(0 if fail == 0 else 2)

    else:
        try:
            video_id = extract_video_id(args.url)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)

        try:
            title, content, lang, lang_code = transcribe_video(
                api, video_id, languages, args.timestamps,
            )
        except (TranscriptsDisabled, NoTranscriptFound):
            print(f"No transcript available for video {video_id}.", file=sys.stderr)
            sys.exit(2)
        except CouldNotRetrieveTranscript as e:
            print(f"Failed to fetch transcript: {e}", file=sys.stderr)
            sys.exit(3)
        except Exception as e:
            print(f"Failed: {e}", file=sys.stderr)
            sys.exit(3)

        print(f"{title} ({lang_code})", file=sys.stderr)

        output_path = args.output
        if not output_path and output_dir:
            output_path = f"{output_dir}/{video_id}.md"

        save_or_print(content, output_path)


if __name__ == "__main__":
    main()
