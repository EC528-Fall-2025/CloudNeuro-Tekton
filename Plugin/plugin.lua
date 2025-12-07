-- Triggers Tekton PipelineRun exactly once per COMPLETE DICOM series

function log(msg)
  print("[orthanc-trigger] " .. msg)
end

-- Track which series has already triggered (persisted across restarts)
local triggered_file = "/tmp/triggered_stable_series.json"
triggered_stable = triggered_stable or {}

-- Load file
do
  local f = io.open(triggered_file, "r")
  if f then
    local content = f:read("*a")
    f:close()
    local ok, parsed = pcall(ParseJson, content)
    if ok and parsed then triggered_stable = parsed end
  end
end

local function save_triggered()
  local f = io.open(triggered_file, "w")
  f:write(DumpJson(triggered_stable))
  f:close()
end

function OnStableSeries(seriesId, tags, metadata)
  log("Series became stable: " .. seriesId)

  -- Skip AI-processed series
  local desc = tags["SeriesDescription"]
  if desc and string.find(desc, "AI Brain Mask") then
    log("Skipping AI output series: " .. desc)
    return
  end

  -- Mark triggered
  triggered_stable[seriesId] = true
  save_triggered()

  log("Triggering Tekton pipeline for stable series: " .. seriesId)


  -- Build Tekton payload

  local patientId = tags["PatientID"] or "unknown"
  local studyId   = tags["StudyID"] or "unknown"
  local SOPClassUID = tags["SOPClassUID"] or ""

  local payload = {
    apiVersion = "tekton.dev/v1",
    kind = "PipelineRun",
    metadata = {
      generateName = "orthanc-to-better-dicom-run-",
      namespace = "chris-students-c9344e"
    },
    spec = {
      pipelineRef = { name = "orthanc-to-better-dicom" },
      params = {
        { name = "orthancUrl", value = "https://orthanc-chris.apps.shift.nerc.mghpcc.org" },
        { name = "orthancAuth", value = "orthanc-720:jennings-minions" },
        { name = "patientId", value = patientId },
        { name = "studyId", value = studyId },
        { name = "seriesId", value = seriesId },
        { name = "SOPClassUID", value = SOPClassUID },
        { name = "pattern", value = "" },
        { name = "maskSuffix", value = "_mask.nii" },
      },
      workspaces = {
        { name = "shared", persistentVolumeClaim = { claimName = "dicom-pvc" } }
      }
    }
  }

  local tmp = "/tmp/payload.json"
  local f = io.open(tmp, "w")
  f:write(DumpJson(payload))
  f:close()


  -- Kubernetes authentication
  local ftoken = io.open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r")
  local token = ftoken:read("*a")
  ftoken:close()

  local url = "https://kubernetes.default.svc/apis/tekton.dev/v1/namespaces/chris-students-c9344e/pipelineruns"

  local cmd = string.format(
    "wget --method=POST --quiet --header='Authorization: Bearer %s' " ..
    "--header='Content-Type: application/json' --body-file=%s --no-check-certificate -O - %s",
    token, tmp, url
  )

  os.execute(cmd)
  log("Tekton pipeline triggered for stable series " .. seriesId)
end
