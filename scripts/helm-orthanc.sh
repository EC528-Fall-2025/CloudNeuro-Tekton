#!/usr/bin/env bash
set -e

# Config
NAMESPACE="chris-students-c9344e"
RELEASE_NAME="orthanc"
CHART_REPO_URL="https://github.com/FNNDSC/charts.git"
CHART_DIR="charts/charts/orthanc"

# 1) Install Helm
echo " Checking Helm installation..."
if ! command -v helm &> /dev/null; then
  if command -v brew &> /dev/null; then
    echo " Installing Helm via Homebrew..."
    brew install helm
  else
    echo " Homebrew not found — installing Helm manually..."
    curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
    chmod 700 get_helm.sh
    ./get_helm.sh
    rm -f get_helm.sh
  fi
else
  echo " Helm already installed: $(helm version --short)"
fi

# 2) Add Helm repos
echo " Adding Helm repos..."
helm repo add fnndsc https://fnndsc.github.io/charts
helm repo update

# 3) Switch to OpenShift project
echo " Switching to OpenShift project: $NAMESPACE"
if ! oc project "$NAMESPACE"; then
  echo "  Failed to switch to namespace '$NAMESPACE'."
  exit 1
fi

# 4) Build chart dependencies
echo " Building Helm dependencies..."
pushd "$CHART_DIR"
helm dependency build
popd

# 5) Deploy Orthanc via Helm
echo " Installing Orthanc Helm chart..."
helm upgrade --install "$RELEASE_NAME" "$CHART_DIR" -f values.yaml

echo " Waiting for Orthanc pod to be ready..."
oc rollout status deployment/$RELEASE_NAME -n "$NAMESPACE"

# 6) Expose route
echo "Ensuring OpenShift route exists..."
if ! oc get route "$RELEASE_NAME" -n "$NAMESPACE"; then
  echo "Creating new route for $RELEASE_NAME..."
  if ! oc expose svc "$RELEASE_NAME" --port=http -n "$NAMESPACE"; then
    echo " Failed to expose route automatically — it may already exist or need manual creation."
  fi
else
  echo "Route already exists — skipping creation."
fi

# 7) Output access info
ROUTE=$(oc get route $RELEASE_NAME -n "$NAMESPACE" -o jsonpath='{.spec.host}' || echo "not-found")
echo
echo " Orthanc deployment completed!"
echo "-------------------------------------------"
echo " Access Orthanc at: https://$ROUTE"
echo " Alternatively, run endpoint test"
echo "   curl https://$ROUTE/system"
echo "-------------------------------------------"
