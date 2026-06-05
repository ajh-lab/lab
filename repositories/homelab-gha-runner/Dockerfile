ARG RUNNER_IMAGE=ghcr.io/actions/actions-runner:latest
ARG HELM_IMAGE=alpine/helm:3.21.0
FROM ${HELM_IMAGE} AS helm

FROM ${RUNNER_IMAGE}

USER root

ARG TARGETARCH
ARG KUBECTL_VERSION=v1.28.15

ENV DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

COPY --from=helm /usr/bin/helm /usr/local/bin/helm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      apt-transport-https \
      bash \
      ca-certificates \
      curl \
      dnsutils \
      gh \
      git \
      gnupg \
      iproute2 \
      iputils-ping \
      jq \
      less \
      lsb-release \
      make \
      netcat-openbsd \
      openssh-client \
      procps \
      python3 \
      python3-pip \
      rsync \
      tar \
      unzip \
      wget \
      yq \
      zip \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl --retry 5 --retry-delay 5 --retry-all-errors --connect-timeout 20 --max-time 300 -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && . /etc/os-release \
    && echo "deb [arch=${TARGETARCH:-arm64} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin \
    && curl --retry 5 --retry-delay 5 --retry-all-errors --connect-timeout 20 --max-time 300 -fsSL "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${TARGETARCH:-arm64}/kubectl" -o /usr/local/bin/kubectl \
    && chmod +x /usr/local/bin/kubectl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER runner

LABEL org.opencontainers.image.title="Homelab GitHub Actions Runner"
LABEL org.opencontainers.image.description="ARM64 ARC runner image for lab k3s with Docker-in-Docker client tooling"
LABEL org.opencontainers.image.source="https://github.com/ajh-lab/homelab-gha-runner"
