#!/bin/bash
set -e

# CloudNeuro Helm Chart Installation Script

echo "====================================="
echo "CloudNeuro Installation Script"
echo "====================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}ERROR: kubectl is not installed${NC}"
        echo "Install from: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi
    echo -e "${GREEN}✓ kubectl found${NC}"
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        echo -e "${RED}ERROR: helm is not installed${NC}"
        echo "Install from: https://helm.sh/docs/intro/install/"
        exit 1
    fi
    echo -e "${GREEN}✓ helm found${NC}"
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}ERROR: Cannot connect to Kubernetes cluster${NC}"
        echo "Please configure kubectl with your cluster credentials"
        exit 1
    fi
    echo -e "${GREEN}✓ Connected to Kubernetes cluster${NC}"
    
    # Check Tekton
    if ! kubectl get crd pipelines.tekton.dev &> /dev/null; then
        echo -e "${YELLOW}WARNING: Tekton Pipelines not found${NC}"
        echo "Do you want to install Tekton Pipelines? (y/n)"
        read -r install_tekton
        if [[ "$install_tekton" == "y" ]]; then
            install_tekton_pipelines
        else
            echo -e "${RED}Tekton is required. Exiting.${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ Tekton Pipelines found${NC}"
    fi
    
    echo ""
}

install_tekton_pipelines() {
    echo "Installing Tekton Pipelines..."
    kubectl apply -f https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml
    echo "Waiting for Tekton to be ready..."
    kubectl wait --for=condition=ready pod -l app=tekton-pipelines-controller -n tekton-pipelines --timeout=300s
    echo -e "${GREEN}✓ Tekton Pipelines installed${NC}"
}

# Main installation
main() {
    check_prerequisites
    
    echo "====================================="
    echo "Installing CloudNeuro Helm Chart"
    echo "====================================="
    echo ""
    
    # Get release name
    read -p "Enter release name [cloudneuro]: " RELEASE_NAME
    RELEASE_NAME=${RELEASE_NAME:-cloudneuro}
    
    # Get namespace
    read -p "Enter namespace [cloudneuro]: " NAMESPACE
    NAMESPACE=${NAMESPACE:-cloudneuro}
    
    # Ask for custom values
    echo ""
    echo "Do you want to use custom values? (y/n)"
    read -r use_custom
    
    HELM_CMD="helm install $RELEASE_NAME ./cloudneuro-chart --create-namespace --namespace $NAMESPACE"
    
    if [[ "$use_custom" == "y" ]]; then
        read -p "Enter path to custom values file: " VALUES_FILE
        if [[ -f "$VALUES_FILE" ]]; then
            HELM_CMD="$HELM_CMD -f $VALUES_FILE"
        else
            echo -e "${RED}ERROR: Values file not found: $VALUES_FILE${NC}"
            exit 1
        fi
    fi
    
    echo ""
    echo "Installing with command:"
    echo "$HELM_CMD"
    echo ""
    
    # Execute helm install
    eval $HELM_CMD
    
    echo ""
    echo -e "${GREEN}====================================="
    echo "Installation Complete!"
    echo "=====================================${NC}"
    echo ""
    echo "Check deployment status:"
    echo "  kubectl get pods -n $NAMESPACE"
    echo ""
    echo "View pipelines:"
    echo "  tkn pipeline list -n $NAMESPACE"
    echo ""
    echo "Access Orthanc:"
    echo "  kubectl port-forward svc/orthanc 8042:8042 -n $NAMESPACE"
    echo "  Then open: http://localhost:8042"
    echo ""
}

# Run main function
main
