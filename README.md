# YouTube Transcript Extractor

Docker CLI tool to extract subtitles/transcripts from YouTube videos.

## Build

```bash
docker build -t yt-transcript .
```

## Usage

```bash
# Auto-save to Obsidian vault (Видео)
docker run --rm -v ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/base/Видео:/obsidian yt-transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Output to stdout
docker run --rm yt-transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Pipe to file on host
docker run --rm yt-transcript "https://www.youtube.com/watch?v=dQw4w9WgXcQ" > transcript.txt

# Specify preferred languages (default: ru, en)
docker run --rm -v ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/base/Видео:/obsidian yt-transcript --lang ru,en "https://youtu.be/dQw4w9WgXcQ"

# With timestamps
docker run --rm -v ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/base/Видео:/obsidian yt-transcript --timestamps "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Save to specific file
docker run --rm -v ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/base/Видео:/obsidian yt-transcript -o /obsidian/my_transcript.txt "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## Limitations

- Private videos cannot be accessed
- Age-restricted videos are not supported
- Videos without any subtitles (manual or auto-generated) will return an error
- Some videos may have transcripts disabled by the uploader
