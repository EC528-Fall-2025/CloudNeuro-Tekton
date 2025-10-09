#!/usr/bin/env bash
set -e

# Config
NAMESPACE="chris-students-c9344e"
RELEASE_NAME="orthanc"
CHART_REPO_URL="https://github.com/FNNDSC/charts.git"
CHART_DIR="charts/charts/orthanc"
INDEX_SIZE="5Gi"
STORAGE_SIZE="10Gi"

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
helm repo add oauth2-proxy https://oauth2-proxy.github.io/manifests || true
helm repo update

# 3) Switch to OpenShift project
echo " Switching to OpenShift project: $NAMESPACE"
if ! oc project "$NAMESPACE"; then
  echo "  Failed to switch to namespace '$NAMESPACE'."
  exit 1
fi

# 4) Clone Orthanc chart if missing
if [ ! -d "$CHART_DIR" ]; then
  echo " Cloning Orthanc Helm chart..."
  git clone "$CHART_REPO_URL"
else
  echo "📦 Orthanc chart already exists, skipping clone."
fi

# 5) Clean old Orthanc resources
echo " Cleaning old Orthanc resources..."
oc delete all -l app.kubernetes.io/instance=$RELEASE_NAME -n "$NAMESPACE" --ignore-not-found 2>/dev/null || true
oc delete pvc -l app.kubernetes.io/instance=$RELEASE_NAME -n "$NAMESPACE" --ignore-not-found
oc delete route "$RELEASE_NAME" -n "$NAMESPACE" --ignore-not-found || true

# 6) Build chart dependencies
echo " Building Helm dependencies..."
pushd "$CHART_DIR" > /dev/null
helm dependency build
popd > /dev/null

# 7) Deploy Orthanc via Helm
echo " Installing Orthanc Helm chart..."
helm install "$RELEASE_NAME" "$CHART_DIR" \
  --namespace "$NAMESPACE" \
  --set persistence.index.enabled=true \
  --set persistence.index.size=$INDEX_SIZE \
  --set persistence.storage.enabled=true \
  --set persistence.storage.size=$STORAGE_SIZE \
  --set config.RemoteAccessAllowed=true \
  --set config.AuthenticationEnabled=false \
  --set oauth2-proxy.enabled=false \
  --set securityContext.fsGroup=999 \
  --set securityContext.runAsUser=999

echo " Waiting for Orthanc pod to be ready..."
oc rollout status deployment/$RELEASE_NAME -n "$NAMESPACE"

# 8) Expose route
echo " Exposing Orthanc via OpenShift route..."
oc expose svc $RELEASE_NAME --port=http -n "$NAMESPACE" || true

ROUTE=$(oc get route $RELEASE_NAME -n "$NAMESPACE" -o jsonpath='{.spec.host}' || echo "not-found")
echo
echo " Orthanc deployment completed!"
echo "-------------------------------------------"
echo " Access Orthanc at: http://$ROUTE"
echo " REST API test:"
echo "   curl -k http://$ROUTE/system"
echo "-------------------------------------------"
