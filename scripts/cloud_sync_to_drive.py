import os
import sys
import json
import time
import re
import argparse
import subprocess
import glob
import urllib.request
import urllib.parse

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DRIVE_FOLDERS = {
    'in.flow': '1z4o-CLLKTEKLQEjocEHkfLURufjv23DI',
    'in.tween': '1SBKikSzF_A_zkW_goxfAASNbIrOPKEU9',
    'in.natural': '17HiMllrOY7wLPBbrdzU7hNahRI5h2cAz',
    'in.mellow': '1v5gs7vgJy6wmO36e1poUQ54BbLdBpe82',
    'in.drip': '1K2tNIYj418UvkCllIKAJCmhPVmMDC_Be'
}

CHUNK_SIZE = 16 * 1024 * 1024  # 16 MiB per chunk

def get_google_access_token():
    client_id = os.environ.get('GDRIVE_CLIENT_ID')
    client_secret = os.environ.get('GDRIVE_CLIENT_SECRET')
    refresh_token = os.environ.get('GDRIVE_REFRESH_TOKEN')

    if not (client_id and client_secret and refresh_token):
        # Fallback to local clasprc if running locally
        clasprc = os.path.expanduser(r'~\.clasprc.json')
        if os.path.exists(clasprc):
            with open(clasprc, 'r', encoding='utf-8') as f:
                creds = json.load(f)['tokens']['default']
                client_id = creds['client_id']
                client_secret = creds['client_secret']
                refresh_token = creds['refresh_token']
        else:
            raise RuntimeError("Missing Google Drive credentials (GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN).")

    data = urllib.parse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())['access_token']

def get_drive_files_in_folder(token, folder_id):
    """List existing files in the Drive folder to prevent duplicates."""
    files = {}
    page_token = None
    while True:
        url = f"https://www.googleapis.com/drive/v3/files?q='{folder_id}'+in+parents+and+trashed=false&fields=nextPageToken,files(id,name,size)&pageSize=1000"
        if page_token:
            url += f"&pageToken={page_token}"
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                for f in data.get('files', []):
                    files[f['name']] = f
                page_token = data.get('nextPageToken')
                if not page_token:
                    break
        except Exception as e:
            print(f"⚠️ Error fetching files list from Drive: {e}", flush=True)
            break
    return files

def upload_file_to_drive(file_path, folder_id, token):
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    print(f"☁️ Uploading to Google Drive: {file_name} ({file_size / (1024*1024):.2f} MB)...", flush=True)

    init_url = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Upload-Content-Type': 'video/mp4'
    }
    meta = {
        'name': file_name,
        'parents': [folder_id],
        'description': f'Auto uploaded via Cloud Pipeline'
    }
    req = urllib.request.Request(init_url, data=json.dumps(meta).encode(), headers=headers, method='POST')
    with urllib.request.urlopen(req) as resp:
        upload_url = resp.headers['Location']

    with open(file_path, 'rb') as f:
        bytes_sent = 0
        start_time = time.time()
        while bytes_sent < file_size:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            range_start = bytes_sent
            range_end = bytes_sent + len(chunk) - 1

            req_chunk = urllib.request.Request(
                upload_url,
                data=chunk,
                headers={
                    'Content-Range': f'bytes {range_start}-{range_end}/{file_size}',
                    'Content-Length': str(len(chunk))
                },
                method='PUT'
            )

            success = False
            for attempt in range(5):
                try:
                    urllib.request.urlopen(req_chunk)
                    success = True
                    break
                except urllib.error.HTTPError as he:
                    if he.code in (200, 201, 308):
                        success = True
                        break
                    elif he.code == 401:
                        token = get_google_access_token()
                        req_chunk.headers['Authorization'] = f'Bearer {token}'
                    time.sleep(2)
                except Exception:
                    time.sleep(2)

            if not success:
                raise RuntimeError(f"Failed uploading chunk {range_start}-{range_end}")

            bytes_sent += len(chunk)
            pct = (bytes_sent / file_size) * 100
            elapsed = time.time() - start_time
            speed = (bytes_sent / (1024 * 1024)) / max(1, elapsed)
            print(f"   ⬆️ Progress: {pct:.1f}% ({bytes_sent/(1024*1024):.1f}/{file_size/(1024*1024):.1f} MB) at {speed:.2f} MB/s", flush=True)

    print(f"✅ Finished uploading {file_name} in {time.time() - start_time:.1f}s!", flush=True)

def sync_channel(channel_name, limit=5, target_video_id=None):
    folder_id = DRIVE_FOLDERS.get(channel_name)
    if not folder_id:
        print(f"❌ Unknown channel: {channel_name}", flush=True)
        return

    print("=" * 70, flush=True)
    print(f"🚀 STARTING CLOUD SYNC FOR CHANNEL: {channel_name}", flush=True)
    print(f"📁 Target Drive Folder: {folder_id}", flush=True)
    print(f"🎯 Target Video Limit: {limit}", flush=True)
    print("=" * 70, flush=True)

    token = get_google_access_token()
    existing_files = get_drive_files_in_folder(token, folder_id)
    print(f"📋 Found {len(existing_files)} existing file(s) in Drive folder.", flush=True)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    videos_json = os.path.join(base_dir, 'channels_videos.json')
    if not os.path.exists(videos_json):
        raise FileNotFoundError(f"Missing {videos_json}")

    with open(videos_json, 'r', encoding='utf-8') as f:
        all_videos = json.load(f)

    channel_vids = [v for v in all_videos.get(channel_name, []) if v.get('type') == 'Video']
    print(f"🎞️ Total full videos available on YouTube: {len(channel_vids)}", flush=True)

    temp_dir = os.path.join(base_dir, 'temp_cloud_downloads')
    os.makedirs(temp_dir, exist_ok=True)

    synced_count = 0
    for v in channel_vids:
        vid_id = v['id']
        title = v['title']

        if target_video_id and vid_id != target_video_id:
            continue

        # Check if already in Drive by checking video ID in filename
        already_uploaded = False
        for fname in existing_files.keys():
            if vid_id in fname:
                already_uploaded = True
                break

        if already_uploaded:
            print(f"⏩ [Skip] {vid_id} - '{title[:45]}...' is ALREADY in Google Drive.", flush=True)
            continue

        print("\n" + "-" * 70, flush=True)
        print(f"📥 [{synced_count + 1}/{limit}] Downloading from YouTube: {vid_id}", flush=True)
        print(f"📌 Title: {title}", flush=True)
        print("-" * 70, flush=True)

        yt_url = f"https://www.youtube.com/watch?v={vid_id}"
        out_template = os.path.join(temp_dir, f"{vid_id} - %(title).80s.%(ext)s")

        # Fast direct download via yt-dlp on cloud
        cmd = [
            'yt-dlp',
            '--extractor-args', 'youtube:player_client=android,ios,web',
            '--js-runtimes', 'node',
            '-f', 'bv*[ext=mp4]+ba*[ext=m4a]/b[ext=mp4]/best',
            '--merge-output-format', 'mp4',
            '--no-playlist',
            '--no-mtime',
            '--retries', '5',
            '-o', out_template,
            yt_url
        ]

        t0 = time.time()
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"❌ yt-dlp error: {res.stderr[-300:]}", flush=True)
            continue

        # Locate downloaded file
        matched_files = glob.glob(os.path.join(temp_dir, f"{vid_id} *.*"))
        if not matched_files:
            print(f"❌ Downloaded file not found for {vid_id}", flush=True)
            continue

        downloaded_file = matched_files[0]
        print(f"⚡ Downloaded in {time.time() - t0:.1f}s ({os.path.getsize(downloaded_file)/(1024*1024):.1f} MB)", flush=True)

        # Upload to Google Drive
        try:
            upload_file_to_drive(downloaded_file, folder_id, token)
            existing_files[os.path.basename(downloaded_file)] = True
            synced_count += 1
        except Exception as e:
            print(f"❌ Upload error: {e}", flush=True)
        finally:
            # Wipe local file immediately to maintain 0 disk usage
            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
                print(f"🧹 Cleaned up temporary cloud file: {os.path.basename(downloaded_file)}", flush=True)

        if synced_count >= limit:
            print(f"\n🏁 Finished batch limit of {limit} videos.", flush=True)
            break

    print(f"\n🎉 Sync completed! Total transferred this run: {synced_count} video(s).", flush=True)

def main():
    parser = argparse.ArgumentParser(description="Cloud YouTube to Google Drive Sync")
    parser.add_argument('--channel', choices=['in.flow', 'in.tween', 'in.natural', 'in.mellow', 'in.drip', 'all'], default='in.drip')
    parser.add_argument('--limit', type=int, default=5, help='Number of videos to transfer')
    parser.add_argument('--video-id', help='Specific YouTube video ID')
    args = parser.parse_args()

    channels = list(DRIVE_FOLDERS.keys()) if args.channel == 'all' else [args.channel]
    for ch in channels:
        sync_channel(ch, limit=args.limit, target_video_id=args.video_id)

if __name__ == '__main__':
    main()
