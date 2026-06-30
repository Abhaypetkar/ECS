#!/bin/bash
# ============================================================
#  CLEANUP SCRIPT - Delete everything to avoid AWS charges
#  Run this in CloudShell when you're done with the demo
# ============================================================

set -e

PROJECT_NAME="audio-dubbing"
AWS_REGION="ap-south-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "============================================================"
echo "  CLEANING UP ALL RESOURCES"
echo "============================================================"

# Step 1: Delete CloudFormation stack (removes VPC, ALB, ECS, etc.)
echo ">>> Deleting CloudFormation stack..."
aws cloudformation delete-stack \
    --stack-name ${PROJECT_NAME}-stack \
    --region ${AWS_REGION}

echo "    Waiting for stack deletion (this takes a few minutes)..."
aws cloudformation wait stack-delete-complete \
    --stack-name ${PROJECT_NAME}-stack \
    --region ${AWS_REGION}

echo "    ✅ Stack deleted"

# Step 2: Delete ECR repository and images
echo ">>> Deleting ECR repository..."
aws ecr delete-repository \
    --repository-name ${PROJECT_NAME} \
    --force \
    --region ${AWS_REGION} \
    2>/dev/null || echo "    (Repository not found, skipping)"

echo "    ✅ ECR repository deleted"

echo ""
echo "============================================================"
echo "  ✅ ALL RESOURCES CLEANED UP!"
echo "  No more AWS charges for this demo."
echo "============================================================"
