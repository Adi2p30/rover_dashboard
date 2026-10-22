# CLAUDE.md

## Documentation bundle (`docs/`)

`docs/` is an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format)
(OKF v0.2) knowledge base for this project, not loose notes. Treat it as a
real part of the codebase: read it before changing things it covers, and
keep it in sync after you change things it covers.

### Start here

Always enter through [`docs/index.md`](docs/index.md) — it links every page
in the bundle, grouped by category. Don't grep around `docs/` cold; the
index tells you which category and page is relevant.

### Structure

- `components/` — what each subsystem (`generator/`, `backend/`,
  `dashboard/`, `broker`, `ros2_sim/`) does and which files implement it.
- `interfaces/` — exact wire contracts: MQTT topics (telemetry, control,
  external-emulator), the HTTP API, the WebSocket frame protocol, ROS 2
  bridge topics.
- `scenarios/` — the fault scenarios the generator can inject.
- `detectors/` — the fault-detection algorithms and their config.
- `alerting/` — alert manager and safe-state publisher behavior.
- `playbooks/` — step-by-step operational tasks (run locally, switch
  scenario, run tests, run the ROS 2 bridge).
- `decisions/` — architecture decision records (e.g. why self-hosted
  MQTT instead of Grafana Cloud / cloud IoT).
- `log.md` — dated changelog of updates to the bundle itself.

### When to read a doc

- Before editing a component, read its page under `components/` first —
  it names the exact files/modules involved and links related interfaces.
- Before touching an MQTT topic, HTTP endpoint, or WebSocket frame shape,
  read the matching page under `interfaces/` — these document the *exact*
  JSON/message shapes, not just a summary.
- Before adding or modifying a fault scenario or detector, read
  `scenarios/index.md` or `detectors/index.md` and the specific page.
- Before making an architecture choice this project has already
  evaluated (hosting, broker choice, platform), check `decisions/` first
  so you don't re-litigate a settled comparison without reading it.

### When to update docs

Code is the source of truth; docs describe it and must not drift. If you
change behavior that a doc page describes (a module's responsibility, a
topic/endpoint/frame shape, a scenario's effect, a detector's config,
alerting logic), update the corresponding page in the same change —
don't leave it to a follow-up.

Each page's frontmatter has a `resource:` field pointing at the source
file/dir it documents — use that to find the page for code you're
touching, and keep the two from diverging.

### Page conventions

Every page uses this frontmatter shape — match it for edits and new pages:

```yaml
---
type: Component | API Endpoint | Fault Scenario | Fault Detector | Decision Record | Playbook
title: <short title>
description: <one-sentence summary>
resource: <relative path to the source this page documents>
tags: [...]
generated: { by: claude-code/claude-sonnet-5, at: <ISO 8601 timestamp> }
---
```

When you edit a page, update its `generated.at` timestamp. When you add a
new page, add it to its category's `index.md` and to `docs/index.md`.

### Always log changes

After any edit, addition, or move within `docs/`, append a dated entry to
[`docs/log.md`](docs/log.md) (new `## YYYY-MM-DD` heading if today doesn't
have one yet) describing what changed, in the existing style: a
**Creation**/**Update** label, a short description, and links to the
affected page(s). This log is how future sessions (and humans) know the
bundle changed without diffing every file — never skip it.
