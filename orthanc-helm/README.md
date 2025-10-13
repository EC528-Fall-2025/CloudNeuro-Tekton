**Happy Helming!**

This is how to run the helm version of deployment on orthanc
`helm install orthanc . -f ./values.yaml`

Might need to run `helm dependency build` if chart.yaml doesn't have the dependecies

---

**To get URL to access ORTHANC**

Run `oc get pods` to find your pod, it will be named like orthanc-test-xxx -> Should be the one that is the youngest in age


Once you find that, run
`oc expose pod <name-of-the-pod> --port=8042 --target-port=8042 --name=orthanc-service-<number>`

I have already taken 2-5 so use other numbers

Then run,
`oc expose service orthanc-service-<number> --name=orthanc-route-<number>`

`oc get route orthanc-route-<number>`

You will get something like
```
NAME              HOST/PORT                                                          PATH   SERVICES            PORT   TERMINATION   WILDCARD
orthanc-route-<number>   orthanc-route-<number>-chris-students-c9344e.apps.shift.nerc.mghpcc.org          orthanc-service-5   8042                 None
```
Take `orthanc-route-<number>-chris-students-c9344e.apps.shift.nerc.mghpcc.org` and run it on browser!!

Username is orthanc, Password is orthanc

