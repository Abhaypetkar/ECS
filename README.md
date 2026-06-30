# Audio Dubbing ECS Demo (with CodeBuild)

A sample project demonstrating **ECS + CodeBuild + Load Balancing + Multi-threading**.
No local Docker needed — everything builds in the cloud!

## Architecture

```
  GitHub Repo                AWS CodeBuild              Amazon ECR
  (Your Code)    ──────►    (Builds Docker)   ──────►  (Stores Image)
       │                                                     │
       │                                                     ▼
       │                  ┌──────────────────┐         ┌──────────┐
       │                  │   ALB (Load      │         │  Pulls   │
       │                  │   Balancer)      │         │  Image   │
       │                  │   Port 80        │         └────┬─────┘
       │                  └────────┬─────────┘              │
       │                           │                        │
       │              ┌────────────┴────────────┐           │
       │              │                         │           │
       │  ┌───────────▼──────────┐  ┌───────────▼──────────┐
       │  │  EC2 Instance 1      │  │  EC2 Instance 2      │
       │  │  Gunicorn Workers:   │  │  Gunicorn Workers:   │
       │  │  ├── Worker 1        │  │  ├── Worker 1        │
       │  │  ├── Worker 2        │  │  ├── Worker 2        │
       │  │  └── Worker 3        │  │  └── Worker 3        │
       │  └──────────────────────┘  └──────────────────────┘
```

## What Each File Does

| File | Purpose |
|------|---------|
| `app.py` | Flask app simulating audio dubbing with multi-threading |
| `Dockerfile` | Containerizes the app with Gunicorn (3 workers × 2 threads) |
| `buildspec.yml` | Tells **CodeBuild** how to build Docker image & push to ECR |
| `cloudformation.yml` | Creates **ALL** AWS resources in one YAML |
| `deploy.sh` | One-command deployment via CloudShell |
| `cleanup.sh` | Deletes everything (avoid charges) |
| `docker-compose.yml` | Local testing (if Docker is available) |
| `test_6_requests.py` | Fires 6 concurrent requests, shows load distribution |

## Deploy to AWS (3 Steps)

### Step 1: Push Code to GitHub
```bash
git init
git add .
git commit -m "ECS demo project"
git branch -M main
git remote add origin https://github.com/Abhaypetkar/ECS.git
git push -u origin main
```

### Step 2: Deploy via CloudShell
1. Open **AWS Console** → Click **CloudShell** icon (>_)
2. Upload `cloudformation.yml` and `deploy.sh`
3. Run:
```bash
chmod +x deploy.sh
./deploy.sh
```

This will:
- ✅ Create ECR repository
- ✅ Create CodeBuild project (pulls from your GitHub)
- ✅ Create VPC, ALB, ECS Cluster with 2 EC2 instances
- ✅ Set up Auto Scaling (CPU > 70% = scale up)
- ✅ Build Docker image via CodeBuild (no local Docker!)
- ✅ Deploy containers to ECS

### Step 3: Test with 6 Concurrent Requests
```bash
# Update BASE_URL in test_6_requests.py to your ALB URL
python test_6_requests.py
```

**Expected Output:**
```
Request #    Audio File                   Handled By Instance
---------------------------------------------------------------------------
1            hindi_speech_copy_1.wav      EC2-Instance-1
2            hindi_speech_copy_2.wav      EC2-Instance-2
3            hindi_speech_copy_3.wav      EC2-Instance-1
4            hindi_speech_copy_4.wav      EC2-Instance-2
5            hindi_speech_copy_5.wav      EC2-Instance-1
6            hindi_speech_copy_6.wav      EC2-Instance-2

✅ LOAD BALANCING IS WORKING!
   EC2-Instance-1  -> 3 tasks  ███████████████
   EC2-Instance-2  -> 3 tasks  ███████████████
```

## Cleanup (Important — Avoid Charges!)
```bash
chmod +x cleanup.sh
./cleanup.sh
```

## Key Concepts for Discussion

| Concept | How It Works |
|---------|-------------|
| **Multi-threading** | Gunicorn runs 3 workers × 2 threads = 6 concurrent tasks per container |
| **Load Balancing** | ALB distributes: Req 1→Instance 1, Req 2→Instance 2, Req 3→Instance 1... |
| **Auto Scaling** | CPU > 70% → ECS adds more containers automatically |
| **CodeBuild** | Builds Docker image in the cloud from GitHub, pushes to ECR |
| **CloudFormation** | Infrastructure as Code — entire setup in one YAML file |
