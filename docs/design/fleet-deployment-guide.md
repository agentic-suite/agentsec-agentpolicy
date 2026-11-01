# Fleet Deployment Guide

Deploy AgentPolicy as a fleet of PDP instances serving authorization decisions across your agent infrastructure.

## Topology

```
                     ┌──────────────────┐
                     │  OPAL Server     │
                     │  (policy source) │
                     └────────┬─────────┘
                              │ policy updates
          ┌───────────────────┼───────────────────┐
          │                   │                   │
   ┌──────┴──────┐    ┌──────┴──────┐    ┌──────┴──────┐
   │ PDP Node 1  │    │ PDP Node 2  │    │ PDP Node 3  │
   │ :8000       │    │ :8000       │    │ :8000       │
   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │ POST /authorize
                    ┌────────┴────────┐
                    │  Load Balancer  │
                    │  (nginx/HAProxy)│
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │   Agent Fleet   │
                    └─────────────────┘
```

## Components

- **PDP Node:** `agentpolicy serve` with `POST /authorize`, audit endpoints, and analytics.
- **OPAL Server:** (optional) distributes policy updates to all PDP nodes.
- **Load Balancer:** routes agent `POST /authorize` requests to healthy PDP nodes.
- **Agent SDK:** Python library or HTTP client (`POST /authorize`).

## Deployment Options

### Single Node (Development)

```bash
agentpolicy serve --port 8000 --policy-path ./agentpolicy.yaml
```

### Multi-Node Fleet (Production)

Each node runs the same `agentpolicy serve` command behind a load balancer:

```bash
# Node 1
agentpolicy serve --port 8000 --host 0.0.0.0 --policy-path /etc/agentpolicy/policy.yaml

# Node 2
agentpolicy serve --port 8000 --host 0.0.0.0 --policy-path /etc/agentpolicy/policy.yaml
```

### With OPAL Sync

```bash
export OPAL_SERVER_URL=https://opal.example.com
agentpolicy serve --port 8000 --host 0.0.0.0
```

The OPAL client subscribes to policy updates and hot-reloads without restarting.

## Load Balancer Configuration (nginx)

```nginx
upstream agentpolicy_pdp {
    least_conn;
    server pdp1.example.com:8000;
    server pdp2.example.com:8000;
    server pdp3.example.com:8000;
}

server {
    listen 443 ssl;
    location /authorize {
        proxy_pass http://agentpolicy_pdp;
        proxy_set_header Host $host;
        proxy_read_timeout 30s;
    }
    location /audit {
        proxy_pass http://agentpolicy_pdp;
    }
}
```

## Health Checks

```bash
# Single node
curl http://localhost:8000/audit/health

# Load balancer endpoint
curl https://pdp.example.com/audit/health
```

## Policy Rollback

```bash
# Roll back to a previous version
agentpolicy policy rollback --version v2 --policy-path /etc/agentpolicy/versions/
```

## Scaling

- **Horizontal:** add more PDP nodes behind the load balancer. Stateless for authorization; audit sinks are per-node (share via Postgres/network filesystem).
- **Vertical:** AgentPolicy is CPU-bound for scoring. Profile with `agentpolicy calibrate report`.

## Monitoring

- **Audit log:** `GET /audit?session=<id>` or aggregate via `GET /api/analytics`.
- **Calibration:** `agentpolicy calibrate report` shows false-allow/escalate rates per tool/env/data_class.
- **Health:** `GET /audit/health` returns uptime, active sessions, and policy version.