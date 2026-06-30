"""
Test Script - Fire 6 Concurrent Dubbing Requests
=================================================
This script sends 6 audio dubbing requests simultaneously
through the load balancer and shows which EC2 instance
handled each request — proving load balancing works.

Usage:
    python test_6_requests.py
"""

import requests
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load balancer URL (Nginx on port 80)
BASE_URL = "http://localhost"

# 6 copies of the same audio file (as mam asked)
AUDIO_FILES = [
    {"audio_file": "hindi_speech_copy_1.wav", "duration": 8},
    {"audio_file": "hindi_speech_copy_2.wav", "duration": 8},
    {"audio_file": "hindi_speech_copy_3.wav", "duration": 8},
    {"audio_file": "hindi_speech_copy_4.wav", "duration": 8},
    {"audio_file": "hindi_speech_copy_5.wav", "duration": 8},
    {"audio_file": "hindi_speech_copy_6.wav", "duration": 8},
]


def submit_dubbing_request(index, audio_data):
    """Submit a single dubbing request through the load balancer"""
    try:
        response = requests.post(
            f"{BASE_URL}/dub",
            json=audio_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        result = response.json()
        return {
            "request_number": index + 1,
            "audio_file": audio_data["audio_file"],
            "task_id": result.get("task_id"),
            "handled_by": result.get("handled_by_instance"),
            "container": result.get("handled_by_container"),
            "status": result.get("status"),
        }
    except Exception as e:
        return {
            "request_number": index + 1,
            "audio_file": audio_data["audio_file"],
            "error": str(e)
        }


def main():
    print("=" * 70)
    print("  ECS LOAD BALANCING DEMO - 6 Concurrent Audio Dubbing Requests")
    print("=" * 70)
    print(f"\nSending 6 requests through Load Balancer at {BASE_URL}")
    print(f"Each request simulates an audio dubbing task\n")

    # ---- Step 1: Fire all 6 requests concurrently ----
    print("--- Submitting 6 dubbing requests simultaneously ---\n")
    results = []

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(submit_dubbing_request, i, audio): i
            for i, audio in enumerate(AUDIO_FILES)
        }
        for future in as_completed(futures):
            results.append(future.result())

    # Sort by request number
    results.sort(key=lambda x: x["request_number"])

    # ---- Step 2: Display distribution ----
    print(f"{'Request #':<12} {'Audio File':<28} {'Handled By Instance':<25} {'Task ID':<10}")
    print("-" * 75)

    instance_count = {}
    for r in results:
        instance = r.get("handled_by", "ERROR")
        instance_count[instance] = instance_count.get(instance, 0) + 1
        print(f"{r['request_number']:<12} {r['audio_file']:<28} {instance:<25} {r.get('task_id', 'N/A'):<10}")

    # ---- Step 3: Show summary ----
    print("\n" + "=" * 70)
    print("  LOAD DISTRIBUTION SUMMARY")
    print("=" * 70)
    for instance, count in sorted(instance_count.items()):
        bar = "█" * (count * 5)
        print(f"  {instance:<25} -> {count} tasks  {bar}")

    total = sum(instance_count.values())
    print(f"\n  Total tasks: {total}")
    print(f"  Instances used: {len(instance_count)}")

    if len(instance_count) > 1:
        print("\n  ✅ LOAD BALANCING IS WORKING!")
        print("     Tasks are distributed across multiple EC2 instances.")
    else:
        print("\n  ⚠️  All tasks went to the same instance.")
        print("     Check if both containers are running.")

    # ---- Step 4: Check task status on each instance ----
    print("\n" + "=" * 70)
    print("  CHECKING TASKS ON EACH INSTANCE (Direct Access)")
    print("=" * 70)

    for port, name in [(5001, "EC2-Instance-1"), (5002, "EC2-Instance-2")]:
        try:
            resp = requests.get(f"http://localhost:{port}/tasks", timeout=5)
            data = resp.json()
            print(f"\n  {name} (port {port}):")
            print(f"    Total tasks handled: {data['total_tasks']}")
            for t in data.get("tasks", []):
                print(f"    - Task {t['task_id']}: {t['audio_file']} "
                      f"[{t['status']}] Thread: {t.get('thread', 'N/A')}")
        except Exception as e:
            print(f"\n  {name} (port {port}): Unable to connect - {e}")


if __name__ == "__main__":
    main()
