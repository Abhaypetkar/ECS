"""
Sample Audio Dubbing Simulator - ECS Demo
Simulates audio dubbing work with multi-threading to demonstrate
ECS load balancing across multiple EC2 instances.
"""

from flask import Flask, jsonify, request
import threading
import time
import uuid
import socket
import os
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Track which instance this is
INSTANCE_ID = os.environ.get("INSTANCE_ID", socket.gethostname())
CONTAINER_ID = socket.gethostname()

# Thread pool for concurrent dubbing tasks (multi-threading)
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 3))
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Store task results
tasks = {}
tasks_lock = threading.Lock()


def simulate_dubbing(task_id, audio_file, duration=10):
    """
    Simulates an audio dubbing task.
    In real scenario, this would be your IndicF5 model inference.
    """
    with tasks_lock:
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["thread"] = threading.current_thread().name

    print(f"[Instance: {INSTANCE_ID}] [Container: {CONTAINER_ID}] "
          f"[Thread: {threading.current_thread().name}] "
          f"Starting dubbing for task {task_id} - file: {audio_file}")

    # Simulate CPU-intensive dubbing work
    time.sleep(duration)

    with tasks_lock:
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["completed_at"] = time.time()

    print(f"[Instance: {INSTANCE_ID}] [Container: {CONTAINER_ID}] "
          f"[Thread: {threading.current_thread().name}] "
          f"Completed dubbing for task {task_id}")


@app.route("/")
def home():
    return jsonify({
        "service": "Audio Dubbing Simulator",
        "instance_id": INSTANCE_ID,
        "container_id": CONTAINER_ID,
        "max_workers": MAX_WORKERS,
        "active_threads": threading.active_count(),
        "status": "running"
    })


@app.route("/health")
def health():
    """Health check endpoint for ECS / ALB"""
    return jsonify({"status": "healthy", "instance": INSTANCE_ID}), 200


@app.route("/dub", methods=["POST"])
def start_dubbing():
    """
    Submit an audio file for dubbing.
    This demonstrates multi-threading - each request is handled
    by a worker thread from the ThreadPoolExecutor.
    """
    data = request.json or {}
    audio_file = data.get("audio_file", "sample_audio.wav")
    duration = data.get("duration", 10)  # simulated processing time

    task_id = str(uuid.uuid4())[:8]

    with tasks_lock:
        tasks[task_id] = {
            "task_id": task_id,
            "audio_file": audio_file,
            "status": "queued",
            "instance_id": INSTANCE_ID,
            "container_id": CONTAINER_ID,
            "submitted_at": time.time(),
            "completed_at": None,
            "thread": None
        }

    # Submit to thread pool (multi-threading!)
    executor.submit(simulate_dubbing, task_id, audio_file, duration)

    return jsonify({
        "task_id": task_id,
        "status": "queued",
        "handled_by_instance": INSTANCE_ID,
        "handled_by_container": CONTAINER_ID,
        "message": f"Dubbing task submitted. Processing with {MAX_WORKERS} workers available."
    }), 202


@app.route("/task/<task_id>")
def get_task(task_id):
    """Check status of a specific dubbing task"""
    with tasks_lock:
        task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)


@app.route("/tasks")
def get_all_tasks():
    """List all tasks handled by this instance"""
    with tasks_lock:
        return jsonify({
            "instance_id": INSTANCE_ID,
            "container_id": CONTAINER_ID,
            "total_tasks": len(tasks),
            "tasks": list(tasks.values())
        })


if __name__ == "__main__":
    print(f"Starting Audio Dubbing Service on Instance: {INSTANCE_ID}, "
          f"Container: {CONTAINER_ID}, Workers: {MAX_WORKERS}")
    app.run(host="0.0.0.0", port=5000, threaded=True)
