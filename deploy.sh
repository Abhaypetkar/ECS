#!/bin/bash
# ============================================================
#  AWS CloudShell Deploy Script (Using CodeBuild - No Local Docker!)
# ============================================================
#
#  Flow: GitHub Repo -> CodeBuild builds Docker -> ECR -> ECS deploys
#
#  Usage (in AWS CloudShell):
#    chmod +x deploy.sh
#    ./deploy.sh
#
# ============================================================

set -e

# ---------- CONFIGURATION ----------
PROJECT_NAME="audio-dubbing"
AWS_REGION="ap-south-1"
GITHUB_REPO="https://github.com/Abhaypetkar/ECS.git"
GITHUB_BRANCH="main"
INSTANCE_TYPE="t2.micro"
DESIRED_INSTANCES=2

# ---------- AUTO-DETECT ----------
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}"

echo "============================================================"
echo "  AWS ECS + CODEBUILD DEPLOYMENT"
echo "============================================================"
echo "  Account:    ${ACCOUNT_ID}"
echo "  Region:     ${AWS_REGION}"
echo "  GitHub:     ${GITHUB_REPO}"
echo "  Branch:     ${GITHUB_BRANCH}"
echo "  ECR:        ${ECR_URI}"
echo "  Instances:  ${DESIRED_INSTANCES}"
echo "============================================================"
echo ""

# ============================================================
#  STEP 1: Deploy CloudFormation Stack
#  Creates: ECR, CodeBuild, VPC, ALB, ECS, Auto Scaling
# ============================================================
echo ">>> STEP 1: Deploying CloudFormation stack..."
echo "    This creates everything: ECR, CodeBuild, VPC, ALB, ECS Cluster, Auto Scaling"
echo "    (Takes 5-10 minutes...)"
echo ""

aws cloudformation deploy \
    --template-file cloudformation.yml \
    --stack-name ${PROJECT_NAME}-stack \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        ProjectName=${PROJECT_NAME} \
        GitHubRepo=${GITHUB_REPO} \
        GitHubBranch=${GITHUB_BRANCH} \
        InstanceType=${INSTANCE_TYPE} \
        DesiredInstances=${DESIRED_INSTANCES} \
    --region ${AWS_REGION}

echo "    ✅ CloudFormation stack deployed!"
echo ""

# ============================================================
#  STEP 2: Trigger CodeBuild (builds Docker image from GitHub)
# ============================================================
echo ">>> STEP 2: Starting CodeBuild..."
echo "    CodeBuild will: Clone GitHub -> Build Docker -> Push to ECR"
echo ""

BUILD_ID=$(aws codebuild start-build \
    --project-name ${PROJECT_NAME}-build \
    --region ${AWS_REGION} \
    --query 'build.id' \
    --output text)

echo "    Build ID: ${BUILD_ID}"
echo "    Waiting for build to complete..."

# Wait for build to finish
while true; do
    STATUS=$(aws codebuild batch-get-builds \
        --ids ${BUILD_ID} \
        --region ${AWS_REGION} \
        --query 'builds[0].buildStatus' \
        --output text)

    if [ "$STATUS" = "SUCCEEDED" ]; then
        echo "    ✅ CodeBuild SUCCEEDED! Docker image pushed to ECR."
        break
    elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "FAULT" ] || [ "$STATUS" = "STOPPED" ]; then
        echo "    ❌ CodeBuild FAILED with status: ${STATUS}"
        echo "    Check logs: AWS Console -> CodeBuild -> ${PROJECT_NAME}-build"
        exit 1
    else
        echo "    ⏳ Build status: ${STATUS}... (waiting 15s)"
        sleep 15
    fi
done

echo ""

# ============================================================
#  STEP 3: Force ECS to use the new image
# ============================================================
echo ">>> STEP 3: Updating ECS service to use new image..."

CLUSTER_NAME=$(aws cloudformation describe-stacks \
    --stack-name ${PROJECT_NAME}-stack \
    --query "Stacks[0].Outputs[?OutputKey=='ClusterName'].OutputValue" \
    --output text \
    --region ${AWS_REGION})

SERVICE_NAME=$(aws cloudformation describe-stacks \
    --stack-name ${PROJECT_NAME}-stack \
    --query "Stacks[0].Outputs[?OutputKey=='ServiceName'].OutputValue" \
    --output text \
    --region ${AWS_REGION})

aws ecs update-service \
    --cluster ${CLUSTER_NAME} \
    --service ${SERVICE_NAME} \
    --force-new-deployment \
    --region ${AWS_REGION} > /dev/null

echo "    ✅ ECS service updated! Deploying new containers..."
echo ""

# ============================================================
#  STEP 4: Get ALB URL
# ============================================================
ALB_URL=$(aws cloudformation describe-stacks \
    --stack-name ${PROJECT_NAME}-stack \
    --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerURL'].OutputValue" \
    --output text \
    --region ${AWS_REGION})

echo "============================================================"
echo "  ✅ DEPLOYMENT COMPLETE!"
echo "============================================================"
echo ""
echo "  Load Balancer URL:  ${ALB_URL}"
echo "  ECS Cluster:        ${CLUSTER_NAME}"
echo "  ECS Service:        ${SERVICE_NAME}"
echo ""
echo "  Wait 2-3 minutes for containers to start, then test:"
echo ""
echo "    curl ${ALB_URL}/"
echo "    curl ${ALB_URL}/health"
echo ""
echo "  Run 6 concurrent dubbing requests:"
echo "    Update BASE_URL in test_6_requests.py to: ${ALB_URL}"
echo "    python3 test_6_requests.py"
echo ""
echo "  Cleanup (delete everything to avoid charges):"
echo "    ./cleanup.sh"
echo "============================================================"
