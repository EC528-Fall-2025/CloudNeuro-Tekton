# Setup Guide: Testing a Toy App on OpenShift CLI

This document explains how to deploy and test a toy application (`figlet-faas`) on OpenShift using the `oc` command-line interface (CLI). The app converts text into ASCII art, and we use it as a simple way to verify that `oc` is installed and working correctly.

## 1. Install the OpenShift CLI (`oc`)
Download the correct `oc` client for your system the OpenShift console

* [Download OC](https://console.apps.shift.nerc.mghpcc.org/command-line-tools)

Unpack the download, then move into the directory where the `oc` binary lives. For example, on macOS/Linux:

* `cd ~/Downloads/oc-cli`

## 2. Authenticate with the Cluster
Log in to the OpenShift cluster using your token. Replace `<yourtoken>` with the token provided by your OpenShift Console:

* `oc login --token=<your-token> --server=https://api.shift.nerc.mghpcc.org:6443`

This step connects your local CLI to the remote OpenShift cluster.

## 3. Clean Up Previous Deployments (Optional)
If you deployed `figlet-faas` before, remove any old resources:

* `oc delete all -l app=figlet-faas`

The `-l app=figlet-faas` flag deletes all objects labeled as part of that application (deployment, service, route, etc.).

## 4. Deploy the App
Use the `oc new-app` command to tell OpenShift to build and run the app from source:
* `oc new-app nodejs:16~https://github.com/FNNDSC/figlet-faas.git`

What happens:
* `nodejs:16` &rarr; tells OpenShift to use the Node.js 16 builder image
* `~https://github.com/...` &rarr; points to the GitHub repo. OpenShift will clone the repo and create a build config, image, deployment, and service.

## 5. Expose the Service
By default, the app runs inside the cluster. To make it reachable from the outside, expose it with a route:
* `oc expose service figlet-faas`

This creates a public URL

## 6. Get the Route
Retrieve the URL assigned by OpenShift:
* `oc get routes`
Look for something like:
* `figlet-faas   figlet-faas-<namespace>.apps.shift.nerc.mghpcc.org`

## 7. Test the App
Call the app with `curl`, passing in a message:
* `curl "http://figlet-faas-<namespace>.apps.shift.nerc.mghpcc.org/?message=Hello"`

You should see ASCII art returned.

If that doesn't work, you can test the backup public instance hosted by CHRIS:
* `curl "https://figlet.chrisproject.org/?message=Hello+World"`


## What is Happening?
* `oc new app`: Automates build + deployment. It uses a Source-to-Image (S2I) workflow: fetches the code, builds it into a container image with Node.js, and deploys it.
* `oc expose service`: Creates a _route_, which maps the internal service to an external hostname.
* `oc get routes`: Lets you discover the actual URL OpenShift assigned to the app.
* `curl`: Verifies the deployment by sending an HTTP request and checking the output.

## References
* [Access the NERC's OpenShift Web Console](https://nerc-project.github.io/nerc-docs/openshift/logging-in/access-the-openshift-web-console/)
* [NERC Command Line Tools](https://console.apps.shift.nerc.mghpcc.org/command-line-tools)
* [FIGlet Toy App Repo](https://github.com/FNNDSC/figlet-faas?tab=readme-ov-file#deployment-on-openshift)
