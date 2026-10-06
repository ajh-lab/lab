# Prometheus Deployment (Helm)

Chart: `prometheus-community/prometheus`
Version: `29.14.0`
Namespace: `observability`

## Access

- URL: `http://192.168.1.80:32091`

## Deploy

```bash
helm upgrade --install prometheus prometheus-community/prometheus \
  --version 29.14.0 \
  -n observability --create-namespace \
  -f k8s/helm/prometheus/values.yaml
```

## Static AI Workstation Scrapes

`values.yaml` includes static scrape jobs for `ai-workstation-evox2`:

- `litellm-ai-workstation`: `192.168.1.123:4001`
- `ai-workstation-node`: `192.168.1.123:9100`
- `ai-workstation-gpu`: `192.168.1.123:9101`

The node exporter and GPU exporter run as user systemd services on the workstation. Dashboard source and exporter code live in the private `lab-monitoring` repository.

## Retention

Prometheus retains samples for up to 90 days, with a 48 GB TSDB size ceiling.
The earlier limit wins: sustained growth may shorten the effective history.
The local-path volume shares the control-plane node filesystem; its 8 GiB PVC
request is not a filesystem quota. Check free space on that node and the
Prometheus TSDB size regularly, and move the database to dedicated storage if
the shared disk can no longer leave adequate headroom.
