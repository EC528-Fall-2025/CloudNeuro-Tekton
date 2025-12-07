# Orthanc-Tekton Plugin Setup
## Overview

This folder enables automatic processing of a new DICOM series using **Orthanc** (a lightweight DICOM server) and **Tekton Pipelines** on Kubernetes/OpenShift. When clinicians upload new imaging studies to Orthanc, the system automatically triggers a Tekton *PipelineRun* that processes the series (e.g., routing data to a downstream tool like PL-Emerald, performing conversions, running models, or preparing data for analysis).

Additionally, it provides a guide walking through:
- Deploying Orthanc via Helm
- Applying your Tekton pipeline
- Installing Lua automation logic
- Triggering PipelineRuns on new DICOM uploads
- Verifying and debugging your setup

This tooling is intended for **medical IT support staff or research engineers** deploying pipeline automation in a clinical research environment. Clinicians use Orthanc normally; this plugin enhances the system behind the scenes.

---

## Purpose and Rationale
Clinical research teams often manage growing volumes of imaging data. Manual exporting, converting, and routing of DICOM series is error‑prone, time‑consuming, and difficult to scale.

This integration provides:
- Hands‑free automation whenever new data arrives
- **Reproducible, containerized processing** using Tekton
- Clear separation of clinical workflow (Orthanc) and computational workflow (Kubernetes)
- **Extensibility**: Lua scripts in Orthanc can define custom triggers, metadata filters, and workflow logic

The goal is to create a **hands‑free, reproducible workflow** in which Orthanc automatically triggers a Tekton pipeline whenever a clinician uploads new imaging data.

## Prerequisites
Before installation, ensure the following tools are available in your environment:
- A Kubernetes or OpenShift cluster
- `kubectl` and/or `oc` CLI configured
- Helm installed
- A working Orthanc image or Helm deployment
- Access permissions to create ConfigMaps, deployments, and Tekton resources

Namespace used in examples: `chris-students-c9344e`.

--- 

## 1. Apply RBAC Permissions (Required Before Orthanc Deployment)
Orthanc needs Kubernetes permissions to create Tekton PipelineRuns when a new DICOM series is uploaded.

Apply the RBAC manifest by running: 
```
oc apply -f orthanc-rbac.yaml -n chris-students-c9344e
```

--- 

## 2. Create Config for Plugin
Before deploying Orthanc, you also need to apply your plugin config containing the Lua script mount paths, startup scripts, etc.

Create the ConfigMap:

```
oc create configmap orthanc-scripts \
  --from-file=plugin.lua=./plugin.lua \
  -n chris-students-c9344e \
  --dry-run=client -o yaml | kubectl apply -f -
```

--- 

## 3. Deploy Orthanc via Helm
**Recommendation**
Edit `helm-orthanc.sh` before running it. Customize the release name and route so your deployment does not conflict with others.

Go to the correct directory:
```
cd ..
cd scripts
```

Deploy Orthanc by running:
```
./helm-orthanc.sh
```

After this, a pod similar to the following naming convention will be created:
```
orthanc-xxxxxxxxxx-xxxxx
```

Verify the pod:
```
oc get pods -n chris-students-c9344e
```
Once the pod is running, Orthanc is ready.

--- 

## 4. Apply the Tekton Pipeline

Go to back the original directory:
```
cd ..
cd Plugin
```

Apply the pipeline definition:
```
oc apply -f tekton.yaml
```

Check if anything is already running (optional if starting from scratch):
```
oc get pipelineruns -n chris-students-c9344e
```

You may see entries like:
```
NAME                              SUCCEEDED   REASON      STARTTIME   COMPLETIONTIME
orthanc-to-better-dicom-run         True        Succeeded   17m         15m
```

> **Note:** If there are existing runs, you can delete them before starting fresh:
```
kubectl delete pipelinerun <pipelinerun-name> -n chris-students-c9344e
kubectl get pods -n chris-students-c9344e
kubectl delete pod <pipelinerun-pod-name> -n chris-students-c9344e
```

---

## 5. Update ConfigMap With Lua Trigger Script
Your Lua script (e.g., `plugin.lua`) defines how Orthanc responds when a new DICOM instance is stored.

Update the ConfigMap:

```
oc create configmap orthanc-scripts \
  --from-file=plugin.lua=./plugin.lua \
  -n chris-students-c9344e \
  --dry-run=client -o yaml | kubectl apply -f -
```

> **Note:** If changes don’t take effect, delete the Orthanc pod and check pods again:

```
oc delete pod <pod-name> -n chris-students-c9344e
oc get pods -n chris-students-c9344e
```
Orthanc will automatically reload the script on pod restart.

---


## 6. Test the Setup

> **Note:** After a DICOM series is uploaded, Orthanc usually takes
> **1–2 minutes** to mark the series as *stable*. The Tekton pipeline
> will be triggered only after this stabilization period.


**Test 1**: Upload a DICOM series to Orthanc.

Upload via:
- Orthanc Web UI
- Orthanc REST API

**Test 2**: Check the logs of the Orthanc pod to see if the pipeline is triggered:
```
oc logs -f <pod-name> -n chris-students-c9344e
```

Log should show something like:
```
W1028 04:57:55.351002       LUA-EVENTS LuaContext.cpp:95] Lua says: [plugin.lua] New DICOM instance stored: 6400e3fb-c20f2de3-705bccc1-9a6fe3b0-987a45b7
W1028 04:57:55.351882       LUA-EVENTS LuaContext.cpp:95] Lua says: [plugin.lua] Triggering pipeline for series: b791ee43-b843b808-f7b7008c-d506b414-bf845bb4
W1028 04:57:55.352197       LUA-EVENTS LuaContext.cpp:95] Lua says: [plugin.lua] Payload JSON:
{"apiVersion":"tekton.dev/v1","kind":"PipelineRun","metadata":{"generateName":"orthanc-to-better-dicom-run-","namespace":"chris-students-c9344e"},"spec":{"params":[{"name":"orthancUrl","value":"https://orthanc-chris.apps.shift.nerc.mghpcc.org"},{"name":"orthancAuth","value":"orthanc-720:jennings-minions"},{"name":"patientId","value":1234578},{"name":"studyId","value":"unknown"},{"name":"seriesId","value":"b791ee43-b843b808-f7b7008c-d506b414-bf845bb4"},{"name":"pattern","value":""},{"name":"maskSuffix","value":"_mask.nii"}],"pipelineRef":{"name":"orthanc-to-better-dicom-run"},"workspaces":[{"name":"shared","persistentVolumeClaim":{"claimName":"dicom-pvc"}}]}}

W1028 04:57:55.352213       LUA-EVENTS LuaContext.cpp:95] Lua says: [plugin.lua] Executing: wget --method=POST --quiet --header='Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IkdoVjFPMHVJdVIyNW1iTHlpT3UteTYwWlN4RkRCdFhsMDRyQlpJTUtLSkkifQ.eyJhdWQiOlsiaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjIl0sImV4cCI6MTc5MzE2MzQ0MCwiaWF0IjoxNzYxNjI3NDQwLCJpc3MiOiJodHRwczovL2t1YmVybmV0ZXMuZGVmYXVsdC5zdmMiLCJqdGkiOiIwNjVlYzE1Yy1lOTA4LTRmYzctYmQwZS1iZDEyZjM0ODAzMDIiLCJrdWJlcm5ldGVzLmlvIjp7Im5hbWVzcGFjZSI6ImNocmlzLXN0dWRlbnRzLWM5MzQ0ZSIsIm5vZGUiOnsibmFtZSI6Indyay0zIiwidWlkIjoiYTVjZTViYzktNzU3Ni00YmY4LTkyM2ItZGUxZWI5NGUzZDgyIn0sInBvZCI6eyJuYW1lIjoia20tdGVzdC1vcnRoYW5jLTg0Nzc3YzQ3Y2Ytd2xja2wiLCJ1aWQiOiI5MTRjNTcxYi1iOGM4LTQzODItOWMxYy1lNWI3YTVlZTdlNmQifSwic2VydmljZWFjY291bnQiOnsibmFtZSI6ImttLXRlc3Qtb3J0aGFuYyIsInVpZCI6IjVkZDE4Mzg2LTI2MjMtNDhmYi04YmE3LWFmYjE2MGQwN2RhNCJ9LCJ3YXJuYWZ0ZXIiOjE3NjE2MzEwNDd9LCJuYmYiOjE3NjE2Mjc0NDAsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpjaHJpcy1zdHVkZW50cy1jOTM0NGU6a20tdGVzdC1vcnRoYW5jIn0.ZWPgENEWC8QAhaL2du_l5yMTrlq9ku55rtXSTp6J78yvFE1CFd3fdpcVY9bD3l21ZdWF2Kv3A0IiEhJf7VVVBG7tTPpzQtSfJjwCX4w3KJ0aoLTIXKQCcocRRlfq1XKGr8uNKFQk_XHD0d_aSh-g-tCzBlBIiYaAE_EU8R1c5Fyi0JDkPcuduyPa7IiMigOr437FwzWpfjKDsu3F_Tr2dxe6FyikLhKR6fvf7IJXM7CHw4cNCbpj6ie44zE7DklOTFHPGPRvPZYulqCGZZu795RTtYOvV_CqakRHhi3FaJAiLsIe7NXax8MtgNZ4MC-nMvWe02oidWXnYvqjg6Znr-wKXLErgYYyxPJKiNpK39s9cqomIOZ-mWgWyTCLFGjx51zSHQaQ7y0jgKXNsxezobh1vjwdXKaOEI5MC9LoTTWGFM4bjapFNbnnMT_820WKg-DfeM9UYMQQ8rIEs-QPv5m1_UXU658e8_SFMLbNrMxvBOy_j7P9ZCvAndf3pTCXG_ZMa1u-3zZWHqZN6DTPnrvcVSdEc5Wv1US4LlbazHBixzZo8iOQJBiAmJvXYE_zAt2-wzDkjLSlB8cPuOYf-hbriN1LTksB3apNPQpK7xk3SG3UcUAdp0hEvY1UWjA5zokE5L6Ta4kk2TuT8tze9aRcBGWIbGyc2sY-KFvo4Us' --header='Content-Type: application/json' --body-file=/tmp/payload.json --no-check-certificate -O - https://kubernetes.default.svc/apis/tekton.dev/v1/namespaces/chris-students-c9344e/pipelineruns
{
  "apiVersion": "tekton.dev/v1",
  "kind": "PipelineRun",
  "metadata": {
    "creationTimestamp": "2025-10-28T04:57:55Z",
    "generateName": "orthanc-to-better-dicom-run-",
              .
              .
              .
        "name": "shared",
        "persistentVolumeClaim": {
          "claimName": "dicom-pvc"
        }
      }
    ]
  }
}W1028 04:57:55.432242       LUA-EVENTS LuaContext.cpp:95] Lua says: [plugin.lua] Triggered Tekton pipeline for series b791ee43-b843b808-f7b7008c-d506b414-bf845bb4
W1028 04:57:55.432454       LUA-EVENTS LuaContext.cpp:95] Lua says: [plugin.lua] New DICOM instance stored: 8bc7f19b-141f4fc6-8e713d19-3a7f2877-c3b8ed6b
W1028 04:57:55.432819       LUA-EVENTS LuaContext.cpp:95] Lua says: [plugin.lua] Series b791ee43-b843b808-f7b7008c-d506b414-bf845bb4 already triggered; skipping.
W1028 04:57:55.432956       LUA-EVENTS LuaContext.cpp:95] Lua says: [plugin.lua] New DICOM instance stored: 7a36514a-78219bf7-cf8b8626-00d9c5c4-40dde177
W1028 04:57:55.433212       LUA-EVENTS LuaContext.cpp:95] Lua says: [plugin.lua] Series b791ee43-b843b808-f7b7008c-d506b414-bf845bb4 already triggered; skipping.

```

**Test 3**: Re-check pipeline runs:
```
kubectl get pipelineruns -n chris-students-c9344e
```
You should see entries like:
```
NAME                           SUCCEEDED   REASON      STARTTIME   COMPLETIONTIME
orthanc-to-better-dicom-run         True        Succeeded   17m         15m
orthanc-to-better-dicom-run-p526l   True        Succeeded   15m         13m
```

This confirms that the conversion completed successfully on the new data.

> **Note:** The Tekton pipeline typically takes **2–4 minutes** to fully
> process the series. If you don’t see it marked as Succeeded
> immediately, wait a few minutes and check again.


---

## 7. Troubleshooting

Ensure plugin.lua is correctly mounted in the Orthanc pod.

Delete the Orthanc pod if necessary to reload the Lua script.

Confirm Tekton pipeline resources are applied in the correct namespace.

If pipeline triggers are too frequent or missing, verify the Lua script logic for OnStoredInstance and that origin['RequestOrigin'] filtering is correct.

---
## 8. Optional: Verify Tekton Pipeline Internals

To inspect what the pipeline is doing internally:

```
kubectl describe pipelinerun <pipelinerun-name> -n chris-students-c9344e
```

Check task logs:
```
kubectl logs <task-pod-name> -n chris-students-c9344e
```
or 
```
kubectl describe taskrun <task-pod-name (i.e.orthanc-to-better-dicom-run-emerald)> -n chris-students-c9344e
```

This can help diagnose failures or misconfigurations.

## Software License
This project is provided under the MIT License, allowing broad reuse, modification, and integration into research and clinical pipeline environments.
