import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.parse

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CHUNK_SIZE = 16 * 1024 * 1024  # 16 MB chunks

def get_google_access_token():
    client_id = os.environ.get('GDRIVE_CLIENT_ID')
    client_secret = os.environ.get('GDRIVE_CLIENT_SECRET')
    refresh_token = os.environ.get('GDRIVE_REFRESH_TOKEN')

    if not (client_id and client_secret and refresh_token):
        clasprc = os.path.expanduser(r'~\.clasprc.json')
        if os.path.exists(clasprc):
            with open(clasprc, 'r', encoding='utf-8') as f:
                creds = json.load(f)['tokens']['default']
                client_id = creds['client_id']
                client_secret = creds['client_secret']
                refresh_token = creds['refresh_token']
        else:
            raise RuntimeError("Missing Google Drive OAuth credentials.")

    data = urllib.parse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())['access_token']

def fetch_files_from_folder(token, folder_id):
    url = f"https://www.googleapis.com/drive/v3/files?q='{folder_id}'+in+parents+and+trashed=false&fields=files(id,name,size,modifiedTime)&orderBy=quotaBytesUsed+desc"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode()).get('files', [])

def download_file(token, file_id, file_name, file_size, target_path):
    print("=" * 65, flush=True)
    print(f"📥 Downloading Master Video from Google Drive Cloud...", flush=True)
    print(f"📌 File: {file_name}", flush=True)
    print(f"📦 Size: {file_size / (1024*1024):.2f} MB", flush=True)
    print(f"🎯 Output: {target_path}", flush=True)
    print("=" * 65, flush=True)

    t0 = time.time()
    dl_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    req = urllib.request.Request(dl_url, headers={'Authorization': f'Bearer {token}'})

    with urllib.request.urlopen(req) as resp:
        with open(target_path, 'wb') as f:
            bytes_dl = 0
            while True:
                chunk = resp.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
                bytes_dl += len(chunk)
                pct = (bytes_dl / file_size) * 100 if file_size else 0
                speed = (bytes_dl / (1024 * 1024)) / max(0.1, time.time() - t0)
                print(f"   ⬇️ {pct:5.1f}% | {bytes_dl/(1024*1024):.1f}/{file_size/(1024*1024):.1f} MB | {speed:6.2f} MB/s", flush=True)

    print(f"✅ Download completed in {time.time() - t0:.1f}s!", flush=True)

def main():
    parser = argparse.ArgumentParser(description="Fetch video from Google Drive for Cloud Live Streaming")
    parser.add_argument('--folder-id', required=True, help='Google Drive Folder ID')
    parser.add_argument('--output-dir', default='media_live', help='Output directory')
    parser.add_argument('--target-filename', default='stream_video.mp4', help='Target output filename')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    target_path = os.path.join(args.output_dir, args.target_filename)

    token = get_google_access_token()
    files = fetch_files_from_folder(token, args.folder_id)

    # Filter out empty or very small files (< 10 MB)
    video_files = [f for f in files if int(f.get('size', 0)) > 10 * 1024 * 1024]

    if not video_files:
        print(f"⚠️ No master video (>10MB) found in folder {args.folder_id}.")
        print("Falling back to default assets if available.")
        sys.exit(1)

    # Pick the largest master video (e.g. Vol 10 / Vol 16)
    chosen_file = video_files[0]
    file_id = chosen_file['id']
    file_name = chosen_file['name']
    file_size = int(chosen_file.get('size', 0))

    download_file(token, file_id, file_name, file_size, target_path)

if __name__ == '__main__':
    main()
