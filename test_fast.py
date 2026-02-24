import os
import random
import subprocess
import time
from datetime import datetime, timedelta
import concurrent.futures

FILE_NAME = "data.txt"

def get_git_config(key, default):
    try:
        result = subprocess.run(["git", "config", key], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return default

NAME = get_git_config("user.name", "W Mir")
EMAIL = get_git_config("user.email", "wajahat.ali.mir@example.com")

try:
    HEAD_HASH = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
except subprocess.CalledProcessError:
    HEAD_HASH = None

def generate_commits(num_commits):
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    
    print(f"Generating {num_commits} commits payload in memory using threads...")
    start_time = time.time()
    
    def producer(start_idx, end_idx):
        payload = bytearray()
        for i in range(start_idx, end_idx):
            random_days = random.randint(0, 6)
            random_hours = random.randint(0, 23)
            random_mins = random.randint(0, 59)
            
            commit_date = start_of_week + timedelta(days=random_days, hours=random_hours, minutes=random_mins)
            timestamp = int(commit_date.timestamp())
            tz_offset = commit_date.strftime("%z")
            if not tz_offset:
                tz_offset = "+0000"
                
            formatted_date = commit_date.strftime('%Y-%m-%dT%H:%M:%S')
            file_content = f"Commit data: {formatted_date}\n".encode('utf-8')
            commit_msg = f"Commit {i+1}\n".encode('utf-8')

            # Build fast-import command
            payload.extend(b"commit refs/heads/main\n")
            payload.extend(f"committer {NAME} <{EMAIL}> {timestamp} {tz_offset}\n".encode('utf-8'))
            if i == 0 and HEAD_HASH:
                payload.extend(f"from {HEAD_HASH}\n".encode('utf-8'))
                
            payload.extend(f"data {len(commit_msg)}\n".encode('utf-8'))
            payload.extend(commit_msg)
            payload.extend(f"M 100644 inline {FILE_NAME}\n".encode('utf-8'))
            payload.extend(f"data {len(file_content)}\n".encode('utf-8'))
            payload.extend(file_content)
            payload.extend(b"\n")
            
        return payload

    num_threads = 8
    chunk_size = num_commits // num_threads
    
    # Due to concurrent futures, we can't guarantee order if we just queue them.
    # To maintain git history order, we should generate them in chunks and join them in order.
    # We will use ThreadPoolExecutor.map to keep order of chunks.
    
    chunks = []
    for t in range(num_threads):
        start_idx = t * chunk_size
        end_idx = num_commits if t == num_threads - 1 else (t + 1) * chunk_size
        chunks.append((start_idx, end_idx))
        
    full_payload = bytearray()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = executor.map(lambda c: producer(c[0], c[1]), chunks)
        for res in results:
            full_payload.extend(res)
            
    generation_time = time.time() - start_time
    print(f"Generated {num_commits} payload in {generation_time:.2f}s")
    
    # Write to process
    print("Streaming to git fast-import...")
    stream_time = time.time()
    
    process = subprocess.Popen(["git", "fast-import", "--quiet"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=full_payload)
    
    if process.returncode != 0:
        print(f"Error during fast-import: {stderr.decode('utf-8')}")
    else:
        import_time = time.time() - stream_time
        duration = time.time() - start_time
        commits_per_sec = num_commits / duration if duration > 0 else 0
        print(f"Successfully imported {num_commits} commits in {import_time:.2f} seconds.")
        print(f"Total time: {duration:.2f} seconds ({commits_per_sec:.2f} commits/sec)")
        
        # Reset current working tree to the latest commit so data.txt is in sync
        subprocess.run(["git", "reset", "--hard", "HEAD"])

if __name__ == "__main__":
    generate_commits(200)
