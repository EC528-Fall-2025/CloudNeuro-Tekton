# Orthanc Tekton Plugin Setup

This guide explains how to set up the Orthanc plugin with Tekton pipelines to automatically process new DICOM series.

---

## Prerequisites

- Kubernetes cluster with `kubectl` and `oc` configured  
- Helm installed  
- Orthanc image or deployment ready  

---

## 1. Deploy Orthanc via Helm

> **Heads up!**  
> To avoid mixing up deployments, I suggest you customize your route and release name.  
> Edit `helm-orthanc.sh` first so it matches your setup.

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

## 2. Apply Tekton Pipeline

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

**Only do this step to your own pipelinerun**

Check if anything is already running (optional if starting from scratch):
```
kubectl get pipelineruns -n chris-students-c9344e
```

You may see entries like:
```
NAME                                SUCCEEDED   REASON      STARTTIME   COMPLETIONTIME
orthanc-to-better-dicom-run-xxxxx   True        Succeeded   2m51s       30s
```

> **Note:** If there are existing runs, you can delete them before starting fresh:
```
kubectl delete pipelinerun <pipelinerun-name> -n chris-students-c9344e
kubectl get pods -n chris-students-c9344e
kubectl delete pod <pipelinerun-pod-name> -n chris-students-c9344e
```
---

## 3. Create Pipelinerun with Lua Script

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

## 4. Test the Setup

**Test 1**: Upload a DICOM series to Orthanc.

**Test 2**: To check if the pipeline has started running or not, run:

```
kubectl get pipelineruns -n chris-students-c9344e
```

You should see entries like:
```
NAME                                SUCCEEDED   REASON      STARTTIME   COMPLETIONTIME
orthanc-to-better-dicom-run-h6tbc   Unknown     Running      5s       

```

This mean your pipeline has started running!!

**Test 3**: To check if the pipeline has run to completion, run:
```
kubectl get pipelineruns -n chris-students-c9344e
```

You should see entries like:
```
NAME                                SUCCEEDED   REASON      STARTTIME   COMPLETIONTIME
orthanc-to-better-dicom-run-h6tbc   True        Succeeded   2m51s       30s

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

