Happy Helming!

This is how to run the helm version of deployment on orthanc
`helm install orthanc . -f ./values.yaml`

Might need to run `helm dependency build` if chart.yaml doesn't have the dependecies
