#!/bin/sh
set -eu
# K3s owns the CoreDNS manifest; only manage its otherwise unspecified replica count.
k3s kubectl scale deployment coredns -n kube-system --replicas=3
k3s kubectl rollout status deployment/coredns -n kube-system --timeout=180s
k3s kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
