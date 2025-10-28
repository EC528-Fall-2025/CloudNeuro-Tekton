# Orthanc Tekton Plugin Setup

This guide explains how to set up the Orthanc plugin with Tekton pipelines to automatically process new DICOM series.

---

## Prerequisites

- Kubernetes cluster with `kubectl` and `oc` configured  
- Helm installed  
- Orthanc image or deployment ready  

---

## 1. Deploy Orthanc via Helm

Run the deployment script:

```
./helm-orthanc.sh
```

After this, a pod named km-test-orthanc-xxxxxxxxxx-xxxxx will be created.

Verify the pod:
```
kubectl get pods -n chris-students-c9344e
```
--- 

## 2. Create ConfigMap with Lua Script

Upload the dummy.lua script to a ConfigMap:

```
kubectl create configmap orthanc-scripts \
  --from-file=dummy.lua=./dummy.lua \
  -n chris-students-c9344e \
  --dry-run=client -o yaml | kubectl apply -f -
```

> **Note:** If changes don’t take effect, delete the Orthanc pod and check pods again:

```
kubectl delete pod <pod-name> -n chris-students-c9344e
kubectl get pods -n chris-students-c9344e
```

---

## 3. Apply Tekton Pipeline

Check if anything is already running (optional if starting from scratch):
```
kubectl get pipelineruns -n chris-students-c9344e
```

You may see entries like:
```
NAME                           SUCCEEDED   REASON      STARTTIME   COMPLETIONTIME
orthanc-to-emerald-run         True        Succeeded   17m         15m
```

> **Note:** If there are existing runs, you can delete them before starting fresh:
```
kubectl delete pipelinerun <pipelinerun-name> -n chris-students-c9344e
kubectl get pods -n chris-students-c9344e
kubectl delete pod <pipelinerun-pod-name> -n chris-students-c9344e
```
---

Apply the Tekton pipeline definition:
```
oc apply -f tekton.yaml
```

Verify the pipeline run:
```
kubectl get pipelineruns -n chris-students-c9344e
```

Wait until the pipeline status shows Succeeded.

```
NAME                           SUCCEEDED   REASON      STARTTIME   COMPLETIONTIME
orthanc-to-emerald-run         True        Succeeded   5m          3m
```

--- 

## 4. Test the Setup

**Test 1**: Upload a DICOM series to Orthanc.

**Test 2**: Check the logs of the Orthanc pod to see if the pipeline is triggered:
```
kubectl logs -f <pod-name> -n chris-students-c9344e
```

Log should show something like:
```
W1028 04:57:55.351002       LUA-EVENTS LuaContext.cpp:95] Lua says: [dummy.lua] New DICOM instance stored: 6400e3fb-c20f2de3-705bccc1-9a6fe3b0-987a45b7
W1028 04:57:55.351882       LUA-EVENTS LuaContext.cpp:95] Lua says: [dummy.lua] Triggering pipeline for series: b791ee43-b843b808-f7b7008c-d506b414-bf845bb4
W1028 04:57:55.352197       LUA-EVENTS LuaContext.cpp:95] Lua says: [dummy.lua] Payload JSON:
{"apiVersion":"tekton.dev/v1","kind":"PipelineRun","metadata":{"generateName":"orthanc-to-emerald-run-","namespace":"chris-students-c9344e"},"spec":{"params":[{"name":"orthancUrl","value":"https://orthanc-chris.apps.shift.nerc.mghpcc.org"},{"name":"orthancAuth","value":"orthanc-720:jennings-minions"},{"name":"patientId","value":1234578},{"name":"studyId","value":"unknown"},{"name":"seriesId","value":"b791ee43-b843b808-f7b7008c-d506b414-bf845bb4"},{"name":"pattern","value":""},{"name":"maskSuffix","value":"_mask.nii"}],"pipelineRef":{"name":"orthanc-to-emerald"},"workspaces":[{"name":"shared","persistentVolumeClaim":{"claimName":"dicom-pvc"}}]}}

W1028 04:57:55.352213       LUA-EVENTS LuaContext.cpp:95] Lua says: [dummy.lua] Executing: wget --method=POST --quiet --header='Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IkdoVjFPMHVJdVIyNW1iTHlpT3UteTYwWlN4RkRCdFhsMDRyQlpJTUtLSkkifQ.eyJhdWQiOlsiaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjIl0sImV4cCI6MTc5MzE2MzQ0MCwiaWF0IjoxNzYxNjI3NDQwLCJpc3MiOiJodHRwczovL2t1YmVybmV0ZXMuZGVmYXVsdC5zdmMiLCJqdGkiOiIwNjVlYzE1Yy1lOTA4LTRmYzctYmQwZS1iZDEyZjM0ODAzMDIiLCJrdWJlcm5ldGVzLmlvIjp7Im5hbWVzcGFjZSI6ImNocmlzLXN0dWRlbnRzLWM5MzQ0ZSIsIm5vZGUiOnsibmFtZSI6Indyay0zIiwidWlkIjoiYTVjZTViYzktNzU3Ni00YmY4LTkyM2ItZGUxZWI5NGUzZDgyIn0sInBvZCI6eyJuYW1lIjoia20tdGVzdC1vcnRoYW5jLTg0Nzc3YzQ3Y2Ytd2xja2wiLCJ1aWQiOiI5MTRjNTcxYi1iOGM4LTQzODItOWMxYy1lNWI3YTVlZTdlNmQifSwic2VydmljZWFjY291bnQiOnsibmFtZSI6ImttLXRlc3Qtb3J0aGFuYyIsInVpZCI6IjVkZDE4Mzg2LTI2MjMtNDhmYi04YmE3LWFmYjE2MGQwN2RhNCJ9LCJ3YXJuYWZ0ZXIiOjE3NjE2MzEwNDd9LCJuYmYiOjE3NjE2Mjc0NDAsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpjaHJpcy1zdHVkZW50cy1jOTM0NGU6a20tdGVzdC1vcnRoYW5jIn0.ZWPgENEWC8QAhaL2du_l5yMTrlq9ku55rtXSTp6J78yvFE1CFd3fdpcVY9bD3l21ZdWF2Kv3A0IiEhJf7VVVBG7tTPpzQtSfJjwCX4w3KJ0aoLTIXKQCcocRRlfq1XKGr8uNKFQk_XHD0d_aSh-g-tCzBlBIiYaAE_EU8R1c5Fyi0JDkPcuduyPa7IiMigOr437FwzWpfjKDsu3F_Tr2dxe6FyikLhKR6fvf7IJXM7CHw4cNCbpj6ie44zE7DklOTFHPGPRvPZYulqCGZZu795RTtYOvV_CqakRHhi3FaJAiLsIe7NXax8MtgNZ4MC-nMvWe02oidWXnYvqjg6Znr-wKXLErgYYyxPJKiNpK39s9cqomIOZ-mWgWyTCLFGjx51zSHQaQ7y0jgKXNsxezobh1vjwdXKaOEI5MC9LoTTWGFM4bjapFNbnnMT_820WKg-DfeM9UYMQQ8rIEs-QPv5m1_UXU658e8_SFMLbNrMxvBOy_j7P9ZCvAndf3pTCXG_ZMa1u-3zZWHqZN6DTPnrvcVSdEc5Wv1US4LlbazHBixzZo8iOQJBiAmJvXYE_zAt2-wzDkjLSlB8cPuOYf-hbriN1LTksB3apNPQpK7xk3SG3UcUAdp0hEvY1UWjA5zokE5L6Ta4kk2TuT8tze9aRcBGWIbGyc2sY-KFvo4Us' --header='Content-Type: application/json' --body-file=/tmp/payload.json --no-check-certificate -O - https://kubernetes.default.svc/apis/tekton.dev/v1/namespaces/chris-students-c9344e/pipelineruns
{
  "apiVersion": "tekton.dev/v1",
  "kind": "PipelineRun",
  "metadata": {
    "creationTimestamp": "2025-10-28T04:57:55Z",
    "generateName": "orthanc-to-emerald-run-",
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
}W1028 04:57:55.432242       LUA-EVENTS LuaContext.cpp:95] Lua says: [dummy.lua] Triggered Tekton pipeline for series b791ee43-b843b808-f7b7008c-d506b414-bf845bb4
W1028 04:57:55.432454       LUA-EVENTS LuaContext.cpp:95] Lua says: [dummy.lua] New DICOM instance stored: 8bc7f19b-141f4fc6-8e713d19-3a7f2877-c3b8ed6b
W1028 04:57:55.432819       LUA-EVENTS LuaContext.cpp:95] Lua says: [dummy.lua] Series b791ee43-b843b808-f7b7008c-d506b414-bf845bb4 already triggered; skipping.
W1028 04:57:55.432956       LUA-EVENTS LuaContext.cpp:95] Lua says: [dummy.lua] New DICOM instance stored: 7a36514a-78219bf7-cf8b8626-00d9c5c4-40dde177
W1028 04:57:55.433212       LUA-EVENTS LuaContext.cpp:95] Lua says: [dummy.lua] Series b791ee43-b843b808-f7b7008c-d506b414-bf845bb4 already triggered; skipping.

```

**Test 3**: Re-check pipeline runs:
```
kubectl get pipelineruns -n chris-students-c9344e
```

You should see entries like:
```
NAME                           SUCCEEDED   REASON      STARTTIME   COMPLETIONTIME
orthanc-to-emerald-run         True        Succeeded   17m         15m
orthanc-to-emerald-run-p526l   True        Succeeded   15m         13m
```

This confirms that the conversion completed successfully on the new data.

---

## 5. Troubleshooting

Ensure dummy.lua is correctly mounted in the Orthanc pod.

Delete the Orthanc pod if necessary to reload the Lua script.

Confirm Tekton pipeline resources are applied in the correct namespace.

If pipeline triggers are too frequent or missing, verify the Lua script logic for OnStoredInstance and that origin['RequestOrigin'] filtering is correct.

---
## 6. Optional: Verify Tekton Pipeline Internals

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
kubectl describe taskrun <task-pod-name (i.e.orthanc-to-emerald-run-emerald)> -n chris-students-c9344e
```

This can help diagnose failures or misconfigurations.


