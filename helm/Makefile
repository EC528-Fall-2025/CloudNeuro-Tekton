.PHONY: help install uninstall upgrade lint template status clean

NAMESPACE ?= cloudneuro
RELEASE_NAME ?= cloudneuro
CHART_DIR = cloudneuro-chart

help: ## Show available commands
	@echo "CloudNeuro Helm Chart - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: ## Lint the Helm chart
	@echo "Linting Helm chart..."
	@helm lint $(CHART_DIR)

template: ## Generate templates without installing
	@echo "Generating templates..."
	@helm template $(RELEASE_NAME) $(CHART_DIR) --namespace $(NAMESPACE)

install: ## Install with default values
	@echo "Installing CloudNeuro..."
	@helm install $(RELEASE_NAME) $(CHART_DIR) \
		--create-namespace \
		--namespace $(NAMESPACE) \
		--wait \
		--timeout 10m

install-minimal: ## Install with minimal configuration
	@echo "Installing CloudNeuro (minimal)..."
	@helm install $(RELEASE_NAME) $(CHART_DIR) \
		--create-namespace \
		--namespace $(NAMESPACE) \
		--values examples/values-minimal.yaml \
		--wait \
		--timeout 10m

install-prod: ## Install with production configuration
	@echo "Installing CloudNeuro (production)..."
	@helm install $(RELEASE_NAME) $(CHART_DIR) \
		--create-namespace \
		--namespace $(NAMESPACE) \
		--values examples/values-production.yaml \
		--wait \
		--timeout 10m

upgrade: ## Upgrade existing installation
	@helm upgrade $(RELEASE_NAME) $(CHART_DIR) \
		--namespace $(NAMESPACE) \
		--wait

uninstall: ## Uninstall CloudNeuro
	@helm uninstall $(RELEASE_NAME) --namespace $(NAMESPACE)
	@echo "CloudNeuro uninstalled. Run 'make clean' to delete namespace."

clean: ## Delete namespace and all resources
	@kubectl delete namespace $(NAMESPACE) --ignore-not-found=true

status: ## Check deployment status
	@echo "=== Helm Release ==="
	@helm list -n $(NAMESPACE)
	@echo ""
	@echo "=== Pods ==="
	@kubectl get pods -n $(NAMESPACE)
	@echo ""
	@echo "=== Services ==="
	@kubectl get svc -n $(NAMESPACE)
	@echo ""
	@echo "=== PVCs ==="
	@kubectl get pvc -n $(NAMESPACE)

logs: ## View Orthanc logs
	@kubectl logs -n $(NAMESPACE) -l app.kubernetes.io/component=orthanc --tail=50 -f

pipelines: ## List Tekton pipelines
	@tkn pipeline list -n $(NAMESPACE)

port-forward: ## Port-forward Orthanc to localhost:8042
	@echo "Port-forwarding Orthanc to http://localhost:8042"
	@echo "Press Ctrl+C to stop"
	@kubectl port-forward svc/orthanc 8042:8042 -n $(NAMESPACE)

dry-run: ## Perform dry-run installation
	@helm install $(RELEASE_NAME) $(CHART_DIR) \
		--namespace $(NAMESPACE) \
		--dry-run \
		--debug
