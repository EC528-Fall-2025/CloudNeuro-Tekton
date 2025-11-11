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

function OnStoredInstance(instanceId, tags, metadata, origin)
  if origin['RequestOrigin'] == 'Lua' then return end

  log("New DICOM instance stored: " .. instanceId)
  local instance_str = RestApiGet('/instances/' .. instanceId)
  local instance = ParseJson(instance_str)

  local seriesId  = instance['ParentSeries']
  local patientId = tags["PatientID"]
  local studyId   = tags["StudyID"]

  if triggered_series[seriesId] then
    log("Series " .. seriesId .. " already triggered; skipping.")
    return
  end

  triggered_series[seriesId] = true
  save_triggered()
  log("Triggering pipeline for series: " .. seriesId)

  local tekton_url = "https://kubernetes.default.svc/apis/tekton.dev/v1/namespaces/chris-students-c9344e/pipelineruns"

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
        { name = "orthancUrl",  value = "https://orthanc-chris.apps.shift.nerc.mghpcc.org" },
        { name = "orthancAuth", value = "orthanc-720:jennings-minions" },
        { name = "patientId",   value = patientId or "unknown" },
        { name = "studyId",     value = studyId or "unknown" },
        { name = "seriesId",    value = seriesId },
        { name = "pattern",     value = "" },
        { name = "maskSuffix",  value = "_mask.nii" },
      },
      workspaces = {
        { name = "shared", persistentVolumeClaim = { claimName = "dicom-pvc" } }
      }
    }
  }

  local payload_json = DumpJson(payload)
  local tmp_file = "/tmp/payload.json"
  local f = io.open(tmp_file, "w")
  f:write(payload_json)
  f:close()

  local ftoken = io.open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r")
  local token = ftoken:read("*a")
  ftoken:close()

  os.execute("sleep 2") -- optional delay

  local cmd = string.format(
    "wget --method=POST --quiet --header='Authorization: Bearer %s' --header='Content-Type: application/json' " ..
    "--body-file=%s --no-check-certificate -O - %s",
    token, tmp_file, tekton_url
  )

  log("Executing: " .. cmd)
  os.execute(cmd)
  log("Triggered Tekton pipeline for series " .. seriesId)
end
