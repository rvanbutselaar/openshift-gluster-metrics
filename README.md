# openshift-gluster-metrics

Python application which exposes GlusterFS metrics (number of brick / number of online brick) using the Prometheus metrics format.

```
oc create serviceaccount openshift-gluster-metrics
oc adm policy add-cluster-role-to-user cluster-admin -z openshift-gluster-metrics
oc new-app https://github.com/rvanbutselaar/openshift-gluster-metrics.git#dev --image-stream=python:latest
oc patch dc/openshift-gluster-metrics --patch '{"spec":{"template":{"spec":{"serviceAccountName": "openshift-gluster-metrics"}}}}'
```
