# Setup Guide: DICOM to NIFTI and Emerald Conversion in OpenShift

This document explains how to download and process imaging data using OpenShift — specifically how to run **pl-dcm2niix** and **pl-emerald** 100% within the OpenShift environment.  
You’ll use the `oc` CLI to deploy and manage the pods that handle conversion and output retrieval.

---

## 1. Log into OpenShift
Authenticate to the NERC OpenShift cluster using your token:

```bash
oc login --token=<your-token> --server=https://api.shift.nerc.mghpcc.org:6443
```

→ This connects your local CLI session to the cluster.

---

## 2. Deploy Conversion Pods
Apply the YAML configurations to create the pods for NIFTI and Emerald downloads.

```bash
oc apply -f nifti-download-pod.yaml
oc apply -f emerald-download-pod.yaml
```

Each pod will:
- Access input data in DICOM format.
- Run conversion pipelines.
- Store the resulting files in its respective container volume.

---

## 3. Copy Results from Pods to Local Machine
Once the pods finish processing, copy the output files from their internal paths to your local computer.  
> Windows users must prefix commands with `MSYS_NO_PATHCONV=1` in Git Bash to prevent path conversion errors.

```bash
MSYS_NO_PATHCONV=1 oc cp chris-students-c9344e/nifti-viewer:/data ./NIFTI_Output
MSYS_NO_PATHCONV=1 oc cp chris-students-c9344e/result-viewer:/results ./Emerald_Output
```

This saves the converted results into local folders:
- `NIFTI_Output/` → contains `.nii.gz` files (from **pl-dcm2niix**)  
- `Emerald_Output/` → contains `.nii` files (from **pl-emerald**)

> **If you see an error like:**
> ```
> error: unable to upgrade connection: container not found ("viewer")
> ```
> That usually means the container is still starting up.  
> Simply **wait a little longer** (10–20 seconds) and run the command again once the pod is fully ready.  
> You can check its status using:
> ```bash
> oc get pods
> ```

---

## 4. Clean Up Pods
After successful download, delete the pods to free up cluster resources:

```bash
oc delete pod nifti-viewer result-viewer -n chris-students-c9344e
```

---

## 5. Verify Outputs
Check your local directories:
```bash
ls NIFTI_Output
ls Emerald_Output
```

You should see:
- `.nii.gz` files in **NIFTI_Output**
- `.nii` files in **Emerald_Output**

---

## 6. Opening NIFTI and Emerald Files in 3D Slicer (Windows)

### Setup
1. **Download and install [3D Slicer](https://www.slicer.org/)**.  
   This software allows viewing and overlaying medical image volumes.

2. **Load your output files:**
   - Open Slicer.
   - Go to `File → Add Data`.
   - Select files from:
     - `NIFTI_Output/` (for `.nii.gz` files)
     - `Emerald_Output/` (for `.nii` files)

3. **Overlay Mask and Original MRI Scan**
   - Open the **View Controllers** tab.
   - Turn on the small rings (link views) so changes affect all three panes.
   - Select both your **mask** and **original MRI**.
   - Adjust **opacity** to 50% for visualization.

4. **3D Rendering**
   - Open the **Volume Rendering** tab.
   - Choose the **original MRI scan (NIFTI file)** to generate a 3D view.

5. *(Optional)* Generate command-line visualizations similar to CHRIS:
   ```bash
   docker run --rm -v <NIFTI path>:/input -v <Emerald path>:/output ghcr.io/fnndsc/pl-emerald:latest emerald --mask-suffix '_mask.nii' --outputs '0.0:_brain.nii,0.2:_overlay02.nii' /input /output
   ```

   This creates three files — masks, extracted brains, and overlayed volumes for visualization.

---

## 7. Notes & Best Practices
- Always verify your namespace (`chris-students-c9344e`) before running commands.  
- Use descriptive pod names (e.g. `nifti-viewer`, `result-viewer`).  
- For debugging:
  ```bash
  oc logs nifti-viewer
  oc logs result-viewer
  ```

---

## References
- [NERC OpenShift Web Console](https://nerc-project.github.io/nerc-docs/openshift/logging-in/access-the-openshift-web-console/)
- [OpenShift Command Line Tools](https://console.apps.shift.nerc.mghpcc.org/command-line-tools)
- [CHRIS Project on GitHub](https://github.com/FNNDSC)
- Related Apps: [`pl-dcm2niix`](https://github.com/FNNDSC/pl-dcm2niix), [`pl-emerald`](https://github.com/FNNDSC/pl-emerald)
- [3D Slicer Official Site](https://www.slicer.org/)
