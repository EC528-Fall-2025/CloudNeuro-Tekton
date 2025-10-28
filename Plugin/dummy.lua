-- dummy.lua
-- Triggers Tekton PipelineRun once per new DICOM series stored in Orthanc

function log(msg)
  print("[dummy.lua] " .. msg)
end

-- Keep track of triggered series (in memory, resets if Orthanc restarts)
triggered_series = triggered_series or {}

function OnStoredInstance(instanceId, tags, metadata, origin)
  -- avoid recursive triggers or Lua-originated uploads
  if origin['RequestOrigin'] == 'Lua' then
    return
  end

  log("New DICOM instance stored: " .. instanceId)

  -- Get instance info
  local instance_str = RestApiGet('/instances/' .. instanceId)
  local instance = ParseJson(instance_str)

  local seriesId  = instance['ParentSeries']
  local patientId = tags["PatientID"]
  local studyId   = tags["StudyID"]

  -- only trigger if this series has not been triggered before
  if triggered_series[seriesId] then
    log("Series " .. seriesId .. " already triggered; skipping.")
    return
  end

  -- mark this series as triggered
  triggered_series[seriesId] = true
  log("Triggering pipeline for series: " .. seriesId)

  -- Tekton API endpoint
  local tekton_url = "https://kubernetes.default.svc/apis/tekton.dev/v1/namespaces/chris-students-c9344e/pipelineruns"

  -- Tekton PipelineRun payload
  local payload = {
    apiVersion = "tekton.dev/v1",
    kind = "PipelineRun",
    metadata = {
      generateName = "orthanc-to-nifti-run-",
      namespace = "chris-students-c9344e"
    },
    spec = {
      pipelineRef = { name = "orthanc-to-nifti" },
      params = {
        { name = "orthancUrl",  value = "https://orthanc-chris.apps.shift.nerc.mghpcc.org" },
        { name = "orthancAuth", value = "orthanc-720:jennings-minions" },
        { name = "patientId",   value = patientId or "unknown"},
        { name = "studyId",     value = studyId or "unknown"},
        { name = "seriesId",    value = seriesId },
      },
      workspaces = {
        { name = "shared", persistentVolumeClaim = { claimName = "dicom-pvc" } }
      }
    }
  }

  -- Convert Lua table to JSON
  local payload_json = DumpJson(payload)

  -- Save payload to temporary file
  local tmp_file = "/tmp/payload.json"
  local f = io.open(tmp_file, "w")
  f:write(payload_json)
  f:close()

  -- Read in-cluster service account token
  local ftoken = io.open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r")
  local token = ftoken:read("*a")
  ftoken:close()

  -- wget command to POST payload to Tekton

  local cmd = string.format(
    "wget --method=POST --quiet --header='Authorization: Bearer %s' --header='Content-Type: application/json' " ..
    "--body-file=%s --no-check-certificate -O - %s",
    token, tmp_file, tekton_url
  )

  log("Payload JSON:\n" .. payload_json)
  log("Executing: " .. cmd)
  os.execute(cmd)
  log("Triggered Tekton pipeline for series " .. seriesId)
end
