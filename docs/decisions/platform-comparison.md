---
type: Decision Record
title: Telemetry platform comparison — Grafana / Cloud IoT vs self-hosted
description: Compares Grafana Cloud, AWS IoT/Azure IoT, and a self-hosted MQTT-native stack for this rover telemetry use case, and records why the project chose self-hosted.
tags: [architecture, observability, mqtt, decision]
status: stable
---

# Telemetry Dashboard Platform Comparison: Grafana / Cloud IoT vs Self-Hosted

## 1. Use case framing

This project simulates a small rover: a few dozen telemetry points (joint
position/torque/temperature, battery, IMU, wheel speed/slip, comms/camera
heartbeats, GPS), sampled at 2–5 Hz, with a requirement for sub-second alerting
and a "safe state" trip when a critical fault is detected. This is
representative of a single-vehicle prototype or lab rover, not a fleet-scale
production deployment — that distinction matters throughout this comparison.

## 2. Evaluation criteria

- **Latency**: time from sensor value to dashboard/alert visibility.
- **Cost**: infra spend at this scale (single vehicle, low data volume) and how it scales with fleet size.
- **Self-hosting effort**: ops burden to stand up and maintain.
- **Alerting / ML support**: built-in anomaly detection, alert routing, on-call integration.
- **Offline / edge suitability**: can it run with no internet (field deployment, comms blackout)?
- **Vendor lock-in**: how hard to migrate off the platform later.

## 3. Grafana Cloud (managed Grafana + Mimir/Loki + Alerting)

**Pros**: mature dashboarding, huge panel/plugin ecosystem, built-in alerting
with multi-channel notification (Slack, PagerDuty, email), free tier covers
small projects, no infra to run.

**Cons**: requires a network path to Grafana Cloud (bad fit for a rover that
loses comms — exactly the scenario this project simulates as a fault!), metrics
ingestion is push-based over HTTP(S)/Prometheus remote-write, not MQTT-native
— needs a bridge (Telegraf, or a custom MQTT→Prometheus exporter). Cost scales
with active series and log volume, which grows fast with per-joint,
high-frequency telemetry.

**Cost shape**: free tier (~10k series, limited logs) covers this demo; a
real multi-rover fleet at 5 Hz would likely exceed it and move into
metered pricing.

## 4. Cloud IoT platforms (AWS IoT Core + Timestream/CloudWatch, Azure IoT Hub + Monitor)

**Pros**: MQTT-native ingestion (AWS IoT Core and Azure IoT Hub both speak
MQTT directly, closest match to this project's transport), device management,
fleet provisioning/OTA, tight integration with managed time-series stores
(Timestream, Azure Time Series Insights) and rules engines for alerting.

**Cons**: steeper learning curve and more moving parts (IoT Core rules,
Lambda/Functions for processing, IAM policies) than a single Grafana
instance; cost is per-message and per-rule-invocation, which adds up quickly
at multi-Hz continuous telemetry rates; still requires connectivity to the
cloud region, so the same offline/comms-loss weakness applies unless paired
with local edge buffering (AWS IoT Greengrass, Azure IoT Edge).

**Cost shape**: pay-per-message pricing (e.g. AWS IoT Core ~$1/million
messages) is cheap at low volume but a rover publishing ~30 topics at 4 Hz is
~120 msg/s ≈ 10M msg/day — this crosses into real monthly cost at fleet
scale, whereas it's negligible for a single prototype.

## 5. Self-hosted OSS (Grafana + InfluxDB/Prometheus, or this project's custom stack)

**Pros**: runs entirely on a local network or even on the rover's own compute
— works during comms blackout, which is a first-class fault scenario here.
No per-message or per-series billing. Full control over retention, schema,
and alert logic. MQTT is the native transport already (Mosquitto), so no
bridging layer needed for a Grafana+InfluxDB setup (Telegraf's MQTT
consumer input plugin writes straight to InfluxDB).

**Cons**: you own uptime, backups, and scaling; Grafana+InfluxDB alerting is
capable but less turnkey than Grafana Cloud's managed alerting; building a
fully custom dashboard (as this project does) means you also own the
frontend, which is more work than dropping panels into Grafana — but buys
full control over layout, safe-state visualization, and detector-driven
color coding that a generic Grafana panel doesn't natively express as
cleanly.

**Cost shape**: hardware/VM cost only; effectively free at this scale on a
laptop or Raspberry Pi-class device.

## 6. Comparison table

| | Grafana Cloud | AWS IoT / Azure IoT | Self-hosted (Grafana+Influx or custom) |
|---|---|---|---|
| Cost at prototype scale | Free tier | Low ($ per msg) | Free (own hardware) |
| Cost at fleet scale | Metered, grows fast | Metered, grows fast | Flat (own infra cost) |
| MQTT-native | No (needs bridge) | Yes | Yes |
| Offline/edge capable | No | Only with edge gateway add-on | Yes, natively |
| Setup effort | Low | Medium-high | Medium |
| Alerting depth | High (managed) | High (rules engine + Lambda/Functions) | Medium (self-built or Grafana alerting) |
| Vendor lock-in | Medium | High | None |

## 7. Recommendation matrix

- **Single prototype/lab rover, iterating fast, always connected**: Grafana
  Cloud free tier via a small MQTT→Prometheus bridge — least setup for
  visualization, though you still need to write the bridge and the safe-state
  logic yourself either way.
- **Fleet-scale production with device management needs**: AWS IoT Core or
  Azure IoT Hub — the device provisioning, OTA, and rules-engine
  infrastructure pays for itself once you're managing many rovers, not one.
- **Field/offline deployment, or where full control over alert logic and
  safe-state behavior matters most**: self-hosted, MQTT-native stack — this
  project's approach (or Grafana+InfluxDB fed by the same Mosquitto broker)
  is the only option that keeps working with zero connectivity, which is
  itself one of the fault scenarios this project simulates.

## 8. Conclusion

This project's choice — a local Mosquitto broker, a lightweight custom
FastAPI/Chart.js dashboard, and statistically simple in-process fault
detection — matches the "field/offline, full control" corner of the matrix:
it needs no cloud dependency, keeps latency and alerting logic entirely
in-house, and is cheap to run. For a real fleet deployment, the natural next
step is either bridging this same MQTT stream into Grafana Cloud/self-hosted
Grafana for richer dashboarding, or migrating device connectivity to AWS
IoT/Azure IoT once fleet management (provisioning, OTA, multi-vehicle
alert routing) becomes the bottleneck rather than dashboarding itself.
