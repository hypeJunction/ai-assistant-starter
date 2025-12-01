#!/usr/bin/env python3
"""Generate slideshow video with TTS narration using edge-tts CLI."""

import json
import subprocess
import os
from pathlib import Path

# Configuration
SLIDES_DIR = Path("assets/slides")
SCRIPTS_DIR = Path("scripts")
OUTPUT_DIR = Path("assets/video-parts")
VOICE = "en-GB-RyanNeural"  # British accent
RATE = "-8%"
EDGE_TTS = "/home/ismayilkhayredinov/.local/bin/edge-tts"

def generate_audio(text: str, output_path: Path):
    """Generate TTS audio using edge-tts CLI."""
    subprocess.run([
        EDGE_TTS,
        "-t", text,
        "-v", VOICE,
        "--rate", RATE,
        "--write-media", str(output_path)
    ], check=True, capture_output=True)
    print(f"  Audio: {output_path.name}")

def get_audio_duration(audio_path: Path) -> float:
    """Get duration of audio file in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())

def create_slide_video(slide_path: Path, audio_path: Path, output_path: Path, duration: float):
    """Create video segment from slide image and audio."""
    total_duration = duration + 1.0  # Add padding

    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(slide_path),
        "-i", str(audio_path),
        "-c:v", "libopenh264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(total_duration),
        "-af", "adelay=500|500,apad=pad_dur=0.5",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#050007",
        str(output_path)
    ], check=True, capture_output=True)
    print(f"  Video: {output_path.name}")

def concatenate_videos(video_paths: list, output_path: Path):
    """Concatenate all video segments into final video."""
    concat_file = OUTPUT_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        for vp in video_paths:
            f.write(f"file '{vp.absolute()}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libopenh264",
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_path)
    ], check=True, capture_output=True)

    concat_file.unlink()
    print(f"\nFinal video: {output_path}")

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(SCRIPTS_DIR / "slide-narrations.json") as f:
        narrations = json.load(f)

    video_segments = []
    print("Generating slide videos...\n")

    for narration in narrations:
        slide_num = narration["slide"]
        text = narration["text"]

        print(f"Slide {slide_num:02d}: {text[:45]}...")

        slide_path = SLIDES_DIR / f"slide.{slide_num:03d}.png"
        audio_path = OUTPUT_DIR / f"audio_{slide_num:02d}.mp3"
        video_path = OUTPUT_DIR / f"segment_{slide_num:02d}.mp4"

        if not slide_path.exists():
            print(f"  Skipping: slide not found")
            continue

        generate_audio(text, audio_path)
        duration = get_audio_duration(audio_path)
        create_slide_video(slide_path, audio_path, video_path, duration)
        video_segments.append(video_path)

    print("\nConcatenating segments...")
    final_output = Path("assets/presentation-video.mp4")
    concatenate_videos(video_segments, final_output)

    print("\nCleaning up...")
    for seg in video_segments:
        seg.unlink()
    for audio in OUTPUT_DIR.glob("audio_*.mp3"):
        audio.unlink()
    OUTPUT_DIR.rmdir()

    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration,size",
         "-of", "json", str(final_output)],
        capture_output=True, text=True
    )
    info = json.loads(result.stdout)
    duration = float(info["format"]["duration"])
    size_mb = int(info["format"]["size"]) / (1024 * 1024)

    print(f"\nDone!")
    print(f"Duration: {int(duration // 60)}:{int(duration % 60):02d}")
    print(f"Size: {size_mb:.1f} MB")

if __name__ == "__main__":
    main()
