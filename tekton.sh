# TASK 1: Download one Orthanc series
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: download-orthanc-series
spec:
  params:
    - name: orthancUrl
      type: string
    - name: orthancAuth
      type: string
    - name: patientId
      type: string
    - name: studyId
      type: string
    - name: seriesId
      type: string
  workspaces:
    - name: shared
  steps:
    - name: download
      image: curlimages/curl:8.7.1
      script: |
        #!/bin/sh
        set -eux
        BASE_DIR="$(workspaces.shared.path)/$(params.patientId)/$(params.studyId)/$(params.seriesId)"
        mkdir -p "${BASE_DIR}"

        ZIP_FILE="${BASE_DIR}/series.zip"
        echo " Downloading series $(params.seriesId) from Orthanc..."
        curl -s -u "$(params.orthancAuth)" \
          "$(params.orthancUrl)/series/$(params.seriesId)/archive" \
          -o "${ZIP_FILE}"

        if [ -s "${ZIP_FILE}" ]; then
          echo " Download complete: ${ZIP_FILE}"
        else
          echo " Empty or failed download."
        fi

    - name: unzip
      image: busybox:1.36.1
      script: |
        #!/bin/sh
        set -eux
        BASE_DIR="$(workspaces.shared.path)/$(params.patientId)/$(params.studyId)/$(params.seriesId)"
        ZIP_FILE="${BASE_DIR}/series.zip"
        if [ -s "${ZIP_FILE}" ]; then
          unzip -o "${ZIP_FILE}" -d "${BASE_DIR}" >/dev/null 2>&1 || true
          rm -f "${ZIP_FILE}"
        fi
        echo " Example DICOMs:"
        find "${BASE_DIR}" -type f -name "*.dcm" | head || true

---

# =====================================
# TASK 2: Convert DICOM → NIFTI
# =====================================
apiVersion: tekton.dev/v1
kind: Task
metadata:
  name: dcm2niix-convert
spec:
  params:
    - name: patientId
      type: string
  workspaces:
    - name: shared
  steps:
    - name: convert
      image: ghcr.io/fnndsc/pl-dcm2niix:latest
      script: |
        #!/bin/sh
        set -eux
        INPUT_DIR="$(workspaces.shared.path)/$(params.patientId)"
        OUTPUT_DIR="$(workspaces.shared.path)/NIFTI"
        mkdir -p "${OUTPUT_DIR}"

        echo " Starting conversion from DICOM → NIFTI..."
        dcm2niix -z y -o "${OUTPUT_DIR}" "${INPUT_DIR}"

        echo " Conversion complete. Example outputs:"
        find "${OUTPUT_DIR}" -type f | head -n 10 || true

---

# =====================================
# PIPELINE: Download → Convert
# =====================================
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: orthanc-to-nifti
spec:
  params:
    - name: orthancUrl
      type: string
    - name: orthancAuth
      type: string
    - name: patientId
      type: string
    - name: studyId
      type: string
    - name: seriesId
      type: string
  workspaces:
    - name: shared
  tasks:
    - name: download
      taskRef:
        name: download-orthanc-series
      params:
        - name: orthancUrl
          value: $(params.orthancUrl)
        - name: orthancAuth
          value: $(params.orthancAuth)
        - name: patientId
          value: $(params.patientId)
        - name: studyId
          value: $(params.studyId)
        - name: seriesId
          value: $(params.seriesId)
      workspaces:
        - name: shared
          workspace: shared

    - name: convert
      runAfter: [download]
      taskRef:
        name: dcm2niix-convert
      params:
        - name: patientId
          value: $(params.patientId)
      workspaces:
        - name: shared
          workspace: shared

---

# =====================================
# PIPELINE RUN
# =====================================
apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  name: orthanc-to-nifti-run
spec:
  pipelineRef:
    name: orthanc-to-nifti
  params:
    - name: orthancUrl
      value: "https://orthanc-chris.apps.shift.nerc.mghpcc.org"
    - name: orthancAuth
      value: "orthanc-720:jennings-minions"
    - name: patientId
      value: "7c222fb2-927d828a-f22f5921-34e89324-80637c0d"
    - name: studyId
      value: "37eccdd3-37e25c5f-1bd55640-81525651-e9b5e18b"
    - name: seriesId
      value: "d06ab3c7-c739be04-509c1388-5381e6c8-7e6e7765"
  workspaces:
    - name: shared
      persistentVolumeClaim:
        claimName: dicom-pvc
