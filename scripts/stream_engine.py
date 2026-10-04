#!/usr/bin/env python3
"""
GitHub Actions 24/7 365-Day Continuous YouTube Live Stream Engine
Handles:
- Ultra-low latency, rock-solid FFmpeg RTMP streaming to YouTube
- Auto-reconnect on network drops
- Automated seamless self-dispatching trigger before the 6-hour GitHub Actions job timeout
"""

import os
import sys
import time
import argparse
import subprocess
import urllib.request
import json

def trigger_next_workflow(repo: str, token: str, workflow_file: str):
    """Triggers the next round of GitHub Actions workflow via GitHub REST API."""
    if not repo or not token or not workflow_file:
        print("[Dispatcher] Missing repo, token, or workflow file. Skipping auto-dispatch.")
        return False
        
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Actions-24-7-Streamer"
    }
    data = json.dumps({"ref": "main"}).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status in [200, 204]:
                print(f"[Dispatcher] ✅ Successfully triggered next 6-hour workflow: {workflow_file}!")
                return True
            else:
                print(f"[Dispatcher] ⚠️ Dispatch response: {resp.status}")
    except Exception as e:
        print(f"[Dispatcher] ❌ Failed to dispatch next workflow: {e}")
    return False

def stream_to_youtube(stream_key: str, media_path: str, audio_path: str, duration_minutes: int, repo: str, token: str, workflow_file: str):
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    print("=" * 65)
    print("🚀 STARTING 24/7 GITHUB ACTIONS CLOUD LIVE STREAM")
    print(f"📁 Media: {media_path} | Audio: {audio_path or 'embedded'}")
    print(f"⏱️ Target Duration: {duration_minutes} minutes")
    print(f"🌐 Target: YouTube Live RTMP Ingestion")
    print("=" * 65)

    max_duration_sec = duration_minutes * 60
    dispatch_trigger_sec = max(60, max_duration_sec - 600)  # 10 mins before end

    if audio_path and os.path.exists(audio_path):
        # Image + Audio mode (Super lightweight & crystal clear)
        ffmpeg_cmd = [
            "ffmpeg",
            "-re",
            "-stream_loop", "-1",
            "-framerate", "1",
            "-loop", "1",
            "-i", media_path,
            "-stream_loop", "-1",
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "stillimage",
            "-b:v", "2800k",
            "-maxrate", "3200k",
            "-bufsize", "6000k",
            "-pix_fmt", "yuv420p",
            "-g", "60",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-f", "flv",
            rtmp_url
        ]
    else:
        # Standard video mode
        ffmpeg_cmd = [
            "ffmpeg",
            "-re",
            "-stream_loop", "-1",
            "-i", media_path,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-b:v", "2800k",
            "-maxrate", "3200k",
            "-bufsize", "6000k",
            "-pix_fmt", "yuv420p",
            "-g", "60",
            "-c:a", "aac",
            "-b:a", "160k",
            "-ar", "44100",
            "-f", "flv",
            rtmp_url
        ]

    start_time = time.time()
    dispatched = False

    while True:
        elapsed = time.time() - start_time
        if elapsed >= max_duration_sec:
            print(f"\n[Streamer] Reached maximum round duration ({duration_minutes}m). Handing over to next job.")
            break

        print(f"\n[Streamer] Launching FFmpeg process (Elapsed: {int(elapsed)}s / {max_duration_sec}s)...")
        proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, errors="replace")

        while proc.poll() is None:
            time.sleep(5)
            elapsed = time.time() - start_time
            
            # Check if it's time to trigger next workflow
            if not dispatched and elapsed >= dispatch_trigger_sec:
                print(f"\n[Streamer] ⏰ Approaching 6h limit (Elapsed: {int(elapsed/60)}m). Triggering next workflow...")
                dispatched = trigger_next_workflow(repo, token, workflow_file)

            if elapsed >= max_duration_sec:
                print("[Streamer] Round time limit reached. Terminating FFmpeg cleanly.")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                break

        if elapsed < max_duration_sec:
            print("[Streamer] ⚠️ Stream disconnected unexpectedly. Auto-restarting in 3 seconds...")
            time.sleep(3)

    print("[Streamer] Round finished successfully. 24/7 stream continuity maintained!")

def main():
    parser = argparse.ArgumentParser(description="24/7 GitHub Actions YouTube Streamer")
    parser.add_argument("--stream-key", required=True, help="YouTube RTMP Stream Key")
    parser.add_argument("--video", required=True, help="Path to looped video file or media")
    parser.add_argument("--audio", default="", help="Optional audio file path for image+audio mode")
    parser.add_argument("--duration", type=int, default=320, help="Duration in minutes per job (default: 320m = 5h20m)")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""), help="GitHub repo (e.g. owner/repo)")
    parser.add_argument("--token", default=os.environ.get("GH_PAT_TOKEN", os.environ.get("GITHUB_TOKEN", "")), help="GitHub token for self-dispatch")
    parser.add_argument("--workflow-file", default="", help="Workflow filename (e.g. live_intween.yml)")
    
    args = parser.parse_args()
    stream_to_youtube(args.stream_key, args.video, args.audio, args.duration, args.repo, args.token, args.workflow_file)

if __name__ == "__main__":
    main()
