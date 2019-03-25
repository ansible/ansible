Wait tests
----------

wait tests require at least one node, and don't work on the normal k8s
openshift-origin container as provided by ansible-test --docker -v k8s

minikube, Kubernetes from Docker or any other Kubernetes service will
suffice.

If kubectl is already using the right config file and context, you can
just do

```
cd test/integration/targets/k8s
./runme.sh -vv
```

otherwise set one or both of `K8S_AUTH_KUBECONFIG` and `K8S_AUTH_CONTEXT`
and use the same command




