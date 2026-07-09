# Prometheus Deployment (Helm)

Chart: `prometheus-community/prometheus`
Version: `29.2.0`
Namespace: `observability`

## Access

- URL: `http://192.168.1.80:32091`

## Deploy

```bash
helm upgrade --install prometheus prometheus-community/prometheus \
  --version 29.2.0 \
  -n observability --create-namespace \
  -f k8s/helm/prometheus/values.yaml
```

## Static AI Workstation Scrapes

`values.yaml` includes static scrape jobs for `ai-workstation-evox2`:

- `litellm-ai-workstation`: `192.168.1.123:4001`
- `ai-workstation-node`: `192.168.1.123:9100`
- `ai-workstation-gpu`: `192.168.1.123:9101`

The node exporter and GPU exporter run as user systemd services on the workstation. Dashboard source and exporter code live in the private `lab-monitoring` repository.
