# CloudNeuro-Tekton Helm Chart

[![Helm](https://img.shields.io/badge/Helm-v3-blue)](https://helm.sh)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.19+-brightgreen)](https://kubernetes.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

One-command deployment of CloudNeuro neuroimaging pipelines on Kubernetes/OpenShift using Helm.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/EC528-Fall-2025/CloudNeuro-Tekton.git
cd CloudNeuro-Tekton/helm

# Install with minimal configuration
helm install cloudneuro cloudneuro-chart \
  --namespace cloudneuro \
  --create-namespace \
  --values examples/values-minimal.yaml
```

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Features

- **One-Command Deployment**: Deploy entire neuroimaging pipeline stack with a single Helm command
- **Orthanc PACS Integration**: Medical imaging storage and DICOM server
- **Tekton Pipelines**: FreeSurfer neuroimaging workflow automation
- **Persistent Storage**: Separate volumes for input, output, and cache data
- **RBAC Security**: Proper service accounts and permissions
- **Multiple Configurations**: Minimal, default, and production value sets
- **Production Ready**: Configurable resources, storage, and scaling

## What Gets Deployed

When you install this Helm chart, the following resources are created:

- **Orthanc PACS Server** - Medical imaging storage (DICOM)
- **Tekton Pipelines** - FreeSurfer neuroimaging workflows
- **Persistent Volumes** - Input data, output data, cache, and Orthanc storage
- **Service Account** - For pipeline execution with proper RBAC
- **Namespace** - Isolated environment for CloudNeuro resources

## Prerequisites

### Required

- **Kubernetes 1.19+** or **OpenShift 4.x**
- **Helm 3.x** - [Installation guide](https://helm.sh/docs/intro/install/)
- **kubectl** - [Installation guide](https://kubernetes.io/docs/tasks/tools/)
- **Tekton Pipelines** - [Will be auto-installed if missing]
- **Storage Provisioner** - For PersistentVolumeClaims

### Optional

- **tkn CLI** - For easier Tekton pipeline management

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/EC528-Fall-2025/CloudNeuro-Tekton.git
cd CloudNeuro-Tekton/helm
```

### Step 2: Validate the Chart

```bash
# Lint the chart
helm lint cloudneuro-chart

# Expected output: "0 chart(s) failed"
```

### Step 3: Install Tekton (if not already installed)

```bash
# Check if Tekton is installed
kubectl get pods -n tekton-pipelines

# If not installed, install it:
kubectl apply -f https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml

# Wait for Tekton to be ready
kubectl wait --for=condition=ready pod \
  -l app=tekton-pipelines-controller \
  -n tekton-pipelines \
  --timeout=300s
```

### Step 4: Install CloudNeuro

Choose one of the following installation options:

#### Option A: Minimal Configuration (Recommended for Testing)

```bash
helm install cloudneuro cloudneuro-chart \
  --namespace cloudneuro \
  --create-namespace \
  --values examples/values-minimal.yaml \
  --wait
```

**Resources**: 8GB RAM, 40GB storage

#### Option B: Default Configuration

```bash
helm install cloudneuro cloudneuro-chart \
  --namespace cloudneuro \
  --create-namespace \
  --wait
```

**Resources**: 16GB RAM, 100GB storage

#### Option C: Production Configuration

```bash
helm install cloudneuro cloudneuro-chart \
  --namespace cloudneuro \
  --create-namespace \
  --values examples/values-production.yaml \
  --wait
```

**Resources**: 64GB RAM, 1.5TB storage

### Step 5: Verify Installation

```bash
# Check all resources
kubectl get all,pvc -n cloudneuro

# Check pod status
kubectl get pods -n cloudneuro

# Expected output:
# NAME                       READY   STATUS    RESTARTS   AGE
# pod/orthanc-xxxx-xxxx      1/1     Running   0          2m
```

## Usage

### Access Orthanc PACS

```bash
# Port-forward Orthanc service
kubectl port-forward svc/orthanc 8042:8042 -n cloudneuro
```

Then open in your browser: **http://localhost:8042**

Default credentials: No authentication required (development mode)

### List Available Pipelines

```bash
# Using kubectl
kubectl get pipeline -n cloudneuro

# Using tkn CLI (if installed)
tkn pipeline list -n cloudneuro
```

### Run FreeSurfer Pipeline

#### Using kubectl

Create a file `pipeline-run.yaml`:

```yaml
apiVersion: tekton.dev/v1beta1
kind: PipelineRun
metadata:
  generateName: freesurfer-run-
  namespace: cloudneuro
spec:
  pipelineRef:
    name: freesurfer-pipeline
  params:
    - name: input-path
      value: "/data/input/subject001"
    - name: subject-id
      value: "subject001"
  workspaces:
    - name: shared-data
      persistentVolumeClaim:
        claimName: cloudneuro-input-data
  serviceAccountName: cloudneuro-pipeline-sa
```

Run it:

```bash
kubectl create -f pipeline-run.yaml
```

#### Using tkn CLI

```bash
tkn pipeline start freesurfer-pipeline \
  --param input-path=/data/input/subject001 \
  --param subject-id=subject001 \
  --workspace name=shared-data,claimName=cloudneuro-input-data \
  --serviceaccount=cloudneuro-pipeline-sa \
  --namespace cloudneuro \
  --showlog
```

### Monitor Pipeline Execution

```bash
# List pipeline runs
kubectl get pipelinerun -n cloudneuro

# Watch pipeline runs
kubectl get pipelinerun -n cloudneuro -w

# View logs
kubectl logs -n cloudneuro -l tekton.dev/pipelineRun --tail=50 -f
```

## Configuration

### Key Configuration Parameters

| Parameter | Description | Default | Minimal | Production |
|-----------|-------------|---------|---------|------------|
| `global.namespace` | Namespace for resources | `cloudneuro` | `cloudneuro-minimal` | `cloudneuro-prod` |
| `orthanc.enabled` | Deploy Orthanc PACS | `true` | `true` | `true` |
| `orthanc.persistence.size` | Orthanc storage | `10Gi` | `5Gi` | `100Gi` |
| `orthanc.resources.limits.memory` | Orthanc memory | `2Gi` | `1Gi` | `8Gi` |
| `tekton.enabled` | Deploy pipelines | `true` | `true` | `true` |
| `tekton.pipelines.freesurfer.enabled` | FreeSurfer pipeline | `true` | `true` | `true` |
| `tekton.pipelines.freesurfer.resources.limits.memory` | FreeSurfer memory | `16Gi` | `8Gi` | `64Gi` |
| `storage.input.size` | Input data storage | `20Gi` | `10Gi` | `500Gi` |
| `storage.output.size` | Output data storage | `50Gi` | `20Gi` | `1Ti` |
| `storage.cache.size` | Cache storage | `30Gi` | `10Gi` | `200Gi` |

### Custom Configuration

Create your own values file:

```yaml
# my-values.yaml
orthanc:
  persistence:
    size: 50Gi
    storageClass: "fast-ssd"
  resources:
    limits:
      memory: "4Gi"
      cpu: "2000m"

tekton:
  pipelines:
    freesurfer:
      resources:
        limits:
          memory: "32Gi"
          cpu: "16000m"

storage:
  input:
    size: 100Gi
  output:
    size: 200Gi
```

Install with custom values:

```bash
helm install cloudneuro cloudneuro-chart \
  --namespace cloudneuro \
  --create-namespace \
  --values my-values.yaml
```

## Upgrading

```bash
# Upgrade with new values
helm upgrade cloudneuro cloudneuro-chart \
  --namespace cloudneuro \
  --values examples/values-production.yaml \
  --wait
```

## Uninstallation

```bash
# Uninstall the release
helm uninstall cloudneuro -n cloudneuro

# Optional: Delete the namespace and all resources
kubectl delete namespace cloudneuro
```

## Troubleshooting

### Common Installation Issues

#### Issue: "cannot re-use a name that is still in use"

**Cause**: A previous Helm release with the same name exists

**Solution**:

```bash
# Check existing releases
helm list -n cloudneuro

# If status is "failed" or you want to start fresh, uninstall:
helm uninstall cloudneuro -n cloudneuro

# Then reinstall
helm install cloudneuro cloudneuro-chart \
  --namespace cloudneuro \
  --values examples/values-minimal.yaml \
  --wait
```

#### Issue: "Namespace already exists and cannot be imported"

**Cause**: Namespace exists but doesn't have required Helm labels

**Solution**:

```bash
# Add required Helm labels to existing namespace
kubectl label namespace cloudneuro app.kubernetes.io/managed-by=Helm
kubectl annotate namespace cloudneuro meta.helm.sh/release-name=cloudneuro
kubectl annotate namespace cloudneuro meta.helm.sh/release-namespace=cloudneuro

# Then install WITHOUT --create-namespace flag
helm install cloudneuro cloudneuro-chart \
  --namespace cloudneuro \
  --values examples/values-minimal.yaml \
  --wait
```

**Alternative**: Delete and recreate the namespace

```bash
# Delete namespace
kubectl delete namespace cloudneuro

# Wait for deletion to complete
kubectl get namespace cloudneuro
# Should return: Error from server (NotFound)

# Create namespace manually
kubectl create namespace cloudneuro

# Add Helm labels
kubectl label namespace cloudneuro app.kubernetes.io/managed-by=Helm
kubectl annotate namespace cloudneuro meta.helm.sh/release-name=cloudneuro
kubectl annotate namespace cloudneuro meta.helm.sh/release-namespace=cloudneuro

# Install
helm install cloudneuro cloudneuro-chart \
  --namespace cloudneuro \
  --values examples/values-minimal.yaml \
  --wait
```

#### Issue: Namespace stuck in "Terminating" state

**Cause**: Resources with finalizers preventing deletion

**Solution**:

```bash
# Force delete the namespace
kubectl delete namespace cloudneuro --force --grace-period=0

# Wait 10-15 seconds, then verify
kubectl get namespace cloudneuro
# Should return: Error from server (NotFound)

# Create fresh namespace with labels
kubectl create namespace cloudneuro
kubectl label namespace cloudneuro app.kubernetes.io/managed-by=Helm
kubectl annotate namespace cloudneuro meta.helm.sh/release-name=cloudneuro
kubectl annotate namespace cloudneuro meta.helm.sh/release-namespace=cloudneuro

# Install
helm install cloudneuro cloudneuro-chart \
  --namespace cloudneuro \
  --values examples/values-minimal.yaml \
  --wait
```

### Storage and Resource Issues

### Issue: PVCs Stuck in Pending

**Cause**: No storage provisioner available

**Solution**:

```bash
# For Minikube
minikube addons enable storage-provisioner

# For Kind
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml

# For OpenShift
# Storage provisioner should already be available
```

### Issue: Orthanc Pod CrashLoopBackOff

**Cause**: Insufficient resources or PVC mounting issues

**Solution**:

```bash
# Check logs
kubectl logs -n cloudneuro -l app.kubernetes.io/component=orthanc

# Increase resources in values.yaml
# Or disable persistence for testing:
helm upgrade cloudneuro cloudneuro-chart \
  --set orthanc.persistence.enabled=false \
  --reuse-values
```

### Issue: Tekton Resources Not Created

**Cause**: Tekton Pipelines not installed or wrong API version

**Solution**:

```bash
# Check Tekton installation
kubectl get pods -n tekton-pipelines

# Install Tekton if missing
kubectl apply -f https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml
```

### Issue: Cannot Access Orthanc UI

**Cause**: Port-forward not running or wrong port

**Solution**:

```bash
# Ensure port-forward is running
kubectl port-forward svc/orthanc 8042:8042 -n cloudneuro

# Check if Orthanc pod is running
kubectl get pods -n cloudneuro -l app.kubernetes.io/component=orthanc
```

### Issue: Pipeline Run Fails

**Cause**: No input data or incorrect paths

**Solution**:

This is expected! The pipeline requires actual DICOM data. The important validation is that:
- The pipeline resources are created
- The pipeline can be started
- The pod starts (even if it fails due to missing data)

## Development

### Directory Structure

```
helm/
├── cloudneuro-chart/          # The Helm chart
│   ├── Chart.yaml            # Chart metadata
│   ├── values.yaml           # Default configuration
│   ├── .helmignore           # Files to exclude from package
│   └── templates/            # Kubernetes resource templates
│       ├── _helpers.tpl      # Template helpers
│       ├── NOTES.txt         # Post-install instructions
│       ├── namespace.yaml    # Namespace definition
│       ├── serviceaccount.yaml
│       ├── rbac.yaml
│       ├── pvc.yaml
│       ├── orthanc.yaml
│       └── tekton-pipeline.yaml
│
├── examples/                  # Example configurations
│   ├── values-minimal.yaml   # Minimal resources
│   └── values-production.yaml # Production resources
│
├── Makefile                   # Build automation (optional)
├── install.sh                 # Interactive installer (optional)
└── README.md                 # This file
```

### Testing Locally

#### Without Cluster (Static Validation)

```bash
# Validate chart structure
helm lint cloudneuro-chart

# Render templates
helm template test cloudneuro-chart --namespace cloudneuro > rendered.yaml

# Check rendered output
cat rendered.yaml
```

#### With Local Cluster (Full Testing)

**Using Minikube**:

```bash
# Start Minikube
minikube start --memory=4096 --cpus=2

# Enable storage
minikube addons enable storage-provisioner

# Install Tekton
kubectl apply -f https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml

# Install chart
helm install cloudneuro cloudneuro-chart \
  --namespace cloudneuro \
  --create-namespace \
  --values examples/values-minimal.yaml
```

**Using Kind**:

```bash
# Create cluster
kind create cluster --name cloudneuro-test

# Install storage provisioner
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml

# Install Tekton
kubectl apply -f https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml

# Install chart
helm install cloudneuro cloudneuro-chart \
  --namespace cloudneuro \
  --create-namespace \
  --values examples/values-minimal.yaml
```

### Package Chart

```bash
# Package the chart
helm package cloudneuro-chart

# Creates: cloudneuro-0.1.0.tgz
```
