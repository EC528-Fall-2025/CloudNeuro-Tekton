-- Triggers Tekton PipelineRun once per new DICOM series stored in Orthanc

function log(msg)
  print("[orthanc-trigger] " .. msg)
end

-- Persistent record of triggered series (survives Orthanc restart)
local triggered_file = "/tmp/triggered_series.json"
triggered_series = triggered_series or {}

-- Load previously triggered series
do
  local f = io.open(triggered_file, "r")
  if f then
    local content = f:read("*a")
    f:close()
    local ok, parsed = pcall(ParseJson, content)
    if ok and parsed then
      triggered_series = parsed
    end
  end
end

local function save_triggered()
  local f = io.open(triggered_file, "w")
  f:write(DumpJson(triggered_series))
  f:close()
end

function OnStableSeries(seriesId, tags, metadata)
  log("Stable series detected: " .. seriesId)

  -- Prevent re-triggering
  if triggered_series[seriesId] then
    log("Series " .. seriesId .. " already triggered; skipping.")
    return
  end

  -- Fetch shared tags for the series
  local sTags_json = RestApiGet('/series/' .. seriesId .. '/shared-tags')
  local sTags = ParseJson(sTags_json)

  local patientId        = sTags["PatientID"] or "unknown"
  local studyId          = sTags["StudyInstanceUID"] or "unknown"
  local seriesDesc       = sTags["SeriesDescription"] or ""
  local SOPClassUID      = sTags["SOPClassUID"] or ""

  -- If this is an EMERALD-generated series → don't trigger pipeline
  if seriesDesc == "AI Brain Mask - EMERALD" then
    log("Series " .. seriesId .. " is EMERALD output; skipping trigger.")
    return
  end

  -- Mark as triggered BEFORE launching pipeline (to avoid double-fire)
  triggered_series[seriesId] = true
  save_triggered()

  log("Triggering pipeline for stable raw series: " .. seriesId)

  -- Tekton API endpoint
  local tekton_url =
    "https://kubernetes.default.svc/apis/tekton.dev/v1/namespaces/chris-students-c9344e/pipelineruns"

  -- PipelineRun payload
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
        { name = "orthancUrl",  value = "https://km-was-here.apps.shift.nerc.mghpcc.org" },
        { name = "orthancAuth", value = "orthanc-720:jennings-minions" },
        { name = "patientId",   value = patientId },
        { name = "studyId",     value = studyId },
     	{ name = "seriesId",    value = seriesId },
        { name = "SOPClassUID", value = SOPClassUID },
        { name = "maskSuffix",  value = "_mask.nii" },
        { name = "pattern",     value = "" },
      },
      workspaces = {
        { name = "shared", persistentVolumeClaim = { claimName = "dicom-pvc" } }
      }
    }
  }

  -- Write JSON payload to temp file
  local tmp_file = "/tmp/payload.json"
  do
    local f = io.open(tmp_file, "w")
    f:write(DumpJson(payload))
    f:close()
  end

  -- Read Kubernetes service account token
  local ftoken = io.open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r")
  local token = ftoken:read("*a")
  ftoken:close()

  os.execute("sleep 2")  -- small safety delay

  -- Execute Tekton API POST
  local cmd = string.format(
    "wget --method=POST --quiet --header='Authorization: Bearer %s' " ..
    "--header='Content-Type: application/json' --body-file=%s " ..
    "--no-check-certificate -O - %s",
    token, tmp_file, tekton_url
  )

  log("Executing Tekton trigger: " .. cmd)
  os.execute(cmd)

  log("Pipeline successfully triggered for series " .. seriesId)
end
