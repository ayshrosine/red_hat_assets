# AssetFlow on OpenShift — Hackathon Implementation Guide

**Goal:** Deploy AssetFlow (FastAPI + React + MongoDB Atlas) onto Red Hat OpenShift
Developer Sandbox in a way that visibly demonstrates every required deliverable, with
a repeatable test plan and a scripted live demo.

**Verdict:** Yes — implementable on your existing repo with light restructuring
(mainly: containerize backend + frontend, add health endpoints, move config into
K8s Secrets/ConfigMaps, add a Knative function for the reminder job). No rewrite needed.

---

## 0. Scope decisions (read this first)

| Deliverable | How we'll satisfy it | Notes |
|---|---|---|
| Git repo | Already have it (`ayshrosine/AssetFlow`) | Just tidy structure, add `/k8s`, `/ci`, `/scripts` folders |
| CI/CD | GitHub Actions → build, test, push image, `oc` deploy | Simpler & more reliable than Tekton for a time-boxed hackathon; mention Tekton as stretch goal |
| K8s/OpenShift manifests | `Deployment`, `Service`, `Route`, `ConfigMap`, `Secret`, `HPA`, `NetworkPolicy`, `PVC`, `ServiceAccount+Role+RoleBinding` | All namespace-scoped (Sandbox has no cluster-admin) |
| Container registry | Quay.io (free, Red Hat's own registry — thematically appropriate) | GHCR also fine |
| Serverless function | Knative Service, triggered by a `PingSource` (cron) | Replaces `scheduler.py`'s `overdue_reminder_loop` — a real fix to a documented bug in your README's "Known Issues" |
| Load balancing | OpenShift `Service` (ClusterIP) + `Route` | Router does round-robin across pod endpoints — no external LB needed/available in Sandbox |
| HPA | `autoscaling/v2 HorizontalPodAutoscaler` on backend Deployment, CPU-based | Sandbox has metrics-server already |
| High availability | 2–3 replicas + `RollingUpdate` strategy + `PodDisruptionBudget` | Demo with continuous curl loop during a redeploy |
| Security | TLS via edge Route, `Secret` for JWT/Mongo URI/OAuth creds, `Role`/`RoleBinding` for a dedicated ServiceAccount, `NetworkPolicy` default-deny + explicit allow | All namespace-scoped, works fine on Sandbox |
| Health probes | `/healthz`, `/readyz`, `/startupz` added to FastAPI | Wired into `livenessProbe`/`readinessProbe`/`startupProbe` |
| Persistent storage | PVC for uploaded files (`storage.py` target dir) | Mongo itself is Atlas (external) — don't spin up Mongo in-cluster |
| Monitoring/logging | Built-in OpenShift **Observe** tab (Dashboards, Metrics, per-pod CPU/mem, Alerts) + structured JSON logs via `deps.py` logger viewable in **Observe → Logs** or `oc logs` | Grafana/Prometheus stack is already there — no need to self-host, Sandbox usually restricts installing your own Prometheus operator |
| Live demo | Scripted 10–12 min walkthrough (Section 8) | |

**Cut for time (mention as future work, don't attempt live):** in-cluster MongoDB,
multi-namespace RBAC, cross-cluster service mesh, custom Grafana.

---

## 1. Prep the repo

```
AssetFlow/
├── backend/                 # existing
├── frontend/                # existing
├── k8s/
│   ├── base/
│   │   ├── backend-deployment.yaml
│   │   ├── backend-service.yaml
│   │   ├── backend-route.yaml
│   │   ├── backend-hpa.yaml
│   │   ├── backend-pdb.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── frontend-service.yaml
│   │   ├── frontend-route.yaml
│   │   ├── secret-template.yaml
│   │   ├── configmap.yaml
│   │   ├── pvc-uploads.yaml
│   │   ├── networkpolicy.yaml
│   │   ├── rbac.yaml
│   │   └── knative-reminder-service.yaml
│   └── kustomization.yaml
├── .github/workflows/ci-cd.yaml
├── backend/Dockerfile
└── frontend/Dockerfile
```

Also fix, per your own README's Known Issues:
- Remove/replace `emergentintegrations` in `backend/requirements.txt` with the
  underlying library (`litellm`) if it's still referenced — it won't be installable
  outside the Emergent sandbox and will break your container build.

---

## 2. Containerize

### `backend/Dockerfile`
```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# OpenShift runs containers with a random non-root UID by default — don't hardcode USER
RUN chgrp -R 0 /app && chmod -R g=u /app
EXPOSE 8000
ENV PORT=8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `frontend/Dockerfile`
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Nginx must not bind to port 80 as root-restricted; OpenShift needs unprivileged port
RUN sed -i 's/listen\s*80;/listen 8080;/' /etc/nginx/conf.d/default.conf \
    && chgrp -R 0 /var/cache/nginx /var/run /usr/share/nginx/html \
    && chmod -R g=u /var/cache/nginx /var/run /usr/share/nginx/html
EXPOSE 8080
```

Build & push locally to confirm before wiring CI:
```bash
docker build -t quay.io/<your-quay-user>/assetflow-backend:dev ./backend
docker build -t quay.io/<your-quay-user>/assetflow-frontend:dev ./frontend
docker login quay.io
docker push quay.io/<your-quay-user>/assetflow-backend:dev
docker push quay.io/<your-quay-user>/assetflow-frontend:dev
```

---

## 3. Health probes (edit `backend/server.py`)

```python
from fastapi import FastAPI, Response
from deps import db  # your existing mongo client

app = FastAPI()

@app.get("/healthz")
def liveness():
    # process is alive — no external calls, keep this cheap
    return {"status": "ok"}

@app.get("/readyz")
async def readiness():
    try:
        await db.command("ping")
        return {"status": "ready"}
    except Exception:
        return Response(status_code=503, content='{"status":"not ready"}',
                         media_type="application/json")

@app.get("/startupz")
async def startup():
    # e.g. confirm seed data / indexes exist
    return {"status": "started"}
```

`k8s/base/backend-deployment.yaml` (probes section):
```yaml
livenessProbe:
  httpGet: { path: /healthz, port: 8000 }
  initialDelaySeconds: 10
  periodSeconds: 15
readinessProbe:
  httpGet: { path: /readyz, port: 8000 }
  initialDelaySeconds: 5
  periodSeconds: 10
startupProbe:
  httpGet: { path: /startupz, port: 8000 }
  failureThreshold: 30
  periodSeconds: 5
```

---

## 4. Full Deployment manifest (backend)

`k8s/base/backend-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: assetflow-backend
  labels: { app: assetflow-backend }
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxUnavailable: 0, maxSurge: 1 }   # zero-downtime
  selector:
    matchLabels: { app: assetflow-backend }
  template:
    metadata:
      labels: { app: assetflow-backend }
    spec:
      serviceAccountName: assetflow-backend-sa
      containers:
        - name: backend
          image: quay.io/<your-quay-user>/assetflow-backend:latest
          ports: [{ containerPort: 8000 }]
          envFrom:
            - configMapRef: { name: assetflow-config }
            - secretRef: { name: assetflow-secrets }
          resources:
            requests: { cpu: "100m", memory: "256Mi" }
            limits:   { cpu: "500m", memory: "512Mi" }
          livenessProbe:  { httpGet: { path: /healthz, port: 8000 }, initialDelaySeconds: 10, periodSeconds: 15 }
          readinessProbe: { httpGet: { path: /readyz,  port: 8000 }, initialDelaySeconds: 5,  periodSeconds: 10 }
          startupProbe:   { httpGet: { path: /startupz, port: 8000 }, failureThreshold: 30, periodSeconds: 5 }
          volumeMounts:
            - { name: uploads, mountPath: /app/uploads }
      volumes:
        - name: uploads
          persistentVolumeClaim: { claimName: assetflow-uploads-pvc }
```

Requests/limits matter a lot here — the Sandbox's quota is small, so an HPA demo needs
low `requests.cpu` (e.g. 100m) so you can actually breach a % threshold with a light
load test tool without hitting the quota ceiling.

`k8s/base/backend-service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata: { name: assetflow-backend, labels: { app: assetflow-backend } }
spec:
  selector: { app: assetflow-backend }
  ports: [{ port: 8000, targetPort: 8000 }]
```

`k8s/base/backend-route.yaml` — this is your **TLS + load balancing** deliverable in one object:
```yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata: { name: assetflow-backend }
spec:
  to: { kind: Service, name: assetflow-backend }
  port: { targetPort: 8000 }
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
```
`oc get route assetflow-backend` gives you an HTTPS URL immediately — router-managed
cert, no cert-manager setup needed for the demo.

Repeat the same three files (Deployment/Service/Route) for the frontend, pointing at
port 8080 and the nginx image.

---

## 5. HPA

`k8s/base/backend-hpa.yaml`
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: assetflow-backend-hpa }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: assetflow-backend }
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource: { name: cpu, target: { type: Utilization, averageUtilization: 60 } }
```

`k8s/base/backend-pdb.yaml` — for HA during rollouts/scale-downs:
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: assetflow-backend-pdb }
spec:
  minAvailable: 1
  selector: { matchLabels: { app: assetflow-backend } }
```

---

## 6. Secrets, ConfigMap, RBAC, NetworkPolicy

`k8s/base/secret-template.yaml` (fill values via `oc create secret` or a sealed-secrets
tool — **never commit real values**):
```yaml
apiVersion: v1
kind: Secret
metadata: { name: assetflow-secrets }
type: Opaque
stringData:
  MONGO_URL: "<from Atlas>"
  JWT_SECRET: "<generate>"
  GOOGLE_CLIENT_SECRET: "<from Google Console>"
  ADMIN_PASSWORD: "<demo-only>"
```
Create it for real like this (don't put secrets in git):
```bash
oc create secret generic assetflow-secrets \
  --from-literal=MONGO_URL="$MONGO_URL" \
  --from-literal=JWT_SECRET="$(openssl rand -hex 32)" \
  --from-literal=GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET" \
  --from-literal=ADMIN_PASSWORD="$ADMIN_PASSWORD"
```

`k8s/base/configmap.yaml`
```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: assetflow-config }
data:
  DB_NAME: "assetflow"
  CORS_ORIGINS: "https://assetflow-frontend-<project>.apps.<cluster-domain>"
  FRONTEND_URL: "https://assetflow-frontend-<project>.apps.<cluster-domain>"
  ENV: "production"
```

`k8s/base/rbac.yaml` — dedicated, least-privilege ServiceAccount instead of `default`:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: assetflow-backend-sa }
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: assetflow-pod-reader }
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]     # e.g. so the app can show its own replica/pod info if you want
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: assetflow-backend-binding }
subjects:
  - kind: ServiceAccount
    name: assetflow-backend-sa
roleRef: { kind: Role, name: assetflow-pod-reader, apiGroup: rbac.authorization.k8s.io }
```

`k8s/base/networkpolicy.yaml` — default-deny then explicit allow (frontend → backend,
router → both, deny everything else):
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-all }
spec:
  podSelector: {}
  policyTypes: [Ingress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-router-to-backend }
spec:
  podSelector: { matchLabels: { app: assetflow-backend } }
  ingress:
    - from:
        - namespaceSelector: { matchLabels: { network.openshift.io/policy-group: ingress } }
      ports: [{ port: 8000, protocol: TCP }]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-router-to-frontend }
spec:
  podSelector: { matchLabels: { app: assetflow-frontend } }
  ingress:
    - from:
        - namespaceSelector: { matchLabels: { network.openshift.io/policy-group: ingress } }
      ports: [{ port: 8080, protocol: TCP }]
```

---

## 7. Persistent storage

`k8s/base/pvc-uploads.yaml`
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: assetflow-uploads-pvc }
spec:
  accessModes: [ReadWriteOnce]   # Sandbox typically only offers RWO — fine for 1 writer pod
  resources: { requests: { storage: 1Gi } }
```
Mounted at `/app/uploads` in the backend Deployment above, and referenced from
`storage.py` so uploaded asset photos/documents persist across pod restarts. Since
`ReadWriteOnce` binds to one node, if you truly need multiple backend replicas all
writing files, either (a) keep uploads on your existing object storage integration and
only use the PVC to demonstrate the pattern, or (b) route all `/upload` traffic to a
single dedicated "uploads" pod behind its own Service. State this trade-off explicitly
in your demo — judges will respect that you know the limitation rather than hiding it.

---

## 8. Serverless: fix the actual documented bug

Your README says:

> `scheduler.py`'s `overdue_reminder_loop` runs as an in-process background loop, which
> does not persist on serverless platforms... convert this to a scheduled HTTP endpoint
> triggered by a cron job.

Do exactly that, using **OpenShift Serverless (Knative)**:

1. Add a plain HTTP endpoint that runs one pass of the reminder logic and exits:
```python
# backend/routers/jobs.py
from fastapi import APIRouter
from emailer import send_overdue_reminders

router = APIRouter()

@router.post("/internal/jobs/overdue-reminders")
async def run_overdue_reminders():
    count = await send_overdue_reminders()
    return {"sent": count}
```
Mount it in `server.py`: `app.include_router(jobs.router)`.

2. Deploy it as a Knative Service (scales to zero when idle — genuinely serverless):

`k8s/base/knative-reminder-service.yaml`
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata: { name: assetflow-reminder-job }
spec:
  template:
    spec:
      containers:
        - image: quay.io/<your-quay-user>/assetflow-backend:latest
          command: ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
          envFrom:
            - configMapRef: { name: assetflow-config }
            - secretRef: { name: assetflow-secrets }
```

3. Trigger it on a schedule with Knative Eventing's `PingSource`:
```yaml
apiVersion: sources.knative.dev/v1
kind: PingSource
metadata: { name: reminder-cron }
spec:
  schedule: "0 * * * *"          # hourly — adjust for demo (e.g. */5 * * * *)
  contentType: "application/json"
  data: '{"trigger":"overdue-reminders"}'
  sink:
    ref:
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: assetflow-reminder-job
      # note: PingSource POSTs to the service root; simplest demo path is to have
      # server.py route root event payloads to the jobs handler, or use a Trigger
      # + Broker if you want proper event filtering
```
This is your **serverless function / event-driven workload** deliverable, and it
literally resolves the caveat in your own README — call that out explicitly in the demo.

---

## 9. CI/CD (GitHub Actions)

`.github/workflows/ci-cd.yaml`
```yaml
name: CI/CD
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: quay.io
          username: ${{ secrets.QUAY_USER }}
          password: ${{ secrets.QUAY_TOKEN }}
      - run: |
          docker build -t quay.io/${{ secrets.QUAY_USER }}/assetflow-backend:${{ github.sha }} ./backend
          docker build -t quay.io/${{ secrets.QUAY_USER }}/assetflow-frontend:${{ github.sha }} ./frontend
          docker push quay.io/${{ secrets.QUAY_USER }}/assetflow-backend:${{ github.sha }}
          docker push quay.io/${{ secrets.QUAY_USER }}/assetflow-frontend:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: redhat-actions/oc-login@v1
        with:
          openshift_server_url: ${{ secrets.OPENSHIFT_SERVER }}
          openshift_token: ${{ secrets.OPENSHIFT_TOKEN }}
          insecure_skip_tls_verify: true
          namespace: ${{ secrets.OPENSHIFT_NAMESPACE }}
      - run: |
          oc set image deployment/assetflow-backend backend=quay.io/${{ secrets.QUAY_USER }}/assetflow-backend:${{ github.sha }}
          oc set image deployment/assetflow-frontend frontend=quay.io/${{ secrets.QUAY_USER }}/assetflow-frontend:${{ github.sha }}
          oc rollout status deployment/assetflow-backend
          oc rollout status deployment/assetflow-frontend
```

Get `OPENSHIFT_TOKEN` from the Sandbox: `oc whoami --show-token` (tokens expire — you'll
likely need to refresh this in GitHub secrets close to demo day since Sandbox sessions
are short-lived). Store all four secrets (`QUAY_USER`, `QUAY_TOKEN`, `OPENSHIFT_SERVER`,
`OPENSHIFT_TOKEN`, `OPENSHIFT_NAMESPACE`) in **GitHub repo → Settings → Secrets → Actions**.

---

## 10. Test plan (what to actually run before demo day)

Run these in order, days before the demo, and again the morning of:

1. **Unit/integration tests** — `cd backend && pytest` (already have `tests/`). Confirm
   it also runs green inside the CI job, not just locally.
2. **Build verification** — both Dockerfiles build clean, containers run locally
   (`docker run -p 8000:8000 ...`) and `/healthz`, `/readyz` return 200.
3. **Deploy verification** — `oc apply -k k8s/base`, then
   `oc get pods -w` until all 3 backend + 2 frontend pods are `Running/Ready`.
4. **Route/TLS check** — `curl -I https://<backend-route>/healthz` → expect `200` and
   a valid TLS handshake (no `-k` needed).
5. **Load balancing proof** — add a `/whoami` debug route returning `os.environ["HOSTNAME"]`,
   then `for i in {1..20}; do curl -s https://<route>/whoami; echo; done` — show
   different pod names responding.
6. **HPA proof** — install `hey` or `k6`, generate sustained load:
   `hey -z 2m -c 50 https://<backend-route>/healthz`, then in a second terminal
   `oc get hpa -w` and `oc get pods -w` — capture a screen recording of replica count
   climbing from 2 → 5/6 and CPU % crossing 60%.
7. **Zero-downtime rollout proof** — run a continuous curl loop
   (`while true; do curl -s -o /dev/null -w "%{http_code}\n" https://<route>/healthz; sleep 0.5; done`)
   in one terminal, trigger `oc rollout restart deployment/assetflow-backend` in another,
   confirm no non-200s appear in the loop.
8. **RBAC check** — `oc auth can-i list pods --as=system:serviceaccount:<ns>:assetflow-backend-sa`
   should be `yes`; `oc auth can-i delete deployments --as=system:serviceaccount:<ns>:assetflow-backend-sa`
   should be `no`.
9. **NetworkPolicy check** — spin up a throwaway pod without the allowed labels
   (`oc run tmp --image=busybox --restart=Never -- sleep 3600`) and confirm
   `oc exec tmp -- wget -qO- assetflow-backend:8000/healthz` **times out**, while
   traffic through the Route still works.
10. **Persistent storage check** — upload a file via the app, `oc delete pod` on the
    backend pod, wait for the replacement, confirm the file is still retrievable.
11. **Serverless check** — `oc get ksvc`, confirm `assetflow-reminder-job` scales to
    zero pods when idle (`oc get pods` shows none), then manually fire the PingSource
    payload or wait for the schedule and confirm a pod appears, runs, and disappears again.
12. **Monitoring check** — OpenShift console → your project → **Observe → Dashboards**
    (per-pod CPU/memory graphs) and **Observe → Metrics** (run a PromQL query like
    `sum(rate(container_cpu_usage_seconds_total{namespace="<ns>"}[5m]))`); also
    `oc logs deployment/assetflow-backend` to show structured logs.

Keep terminal recordings/screenshots of steps 5–12 — live network demos can flake in
front of judges, so a backup recording is worth having even if you also do it live.

---

## 11. Live demo script (~10–12 minutes)

1. **(1 min)** One slide: architecture diagram (frontend/backend/Mongo Atlas/Knative
   job), and the roles slide you already have (Developer/DevOps/Cloud/Security/Troubleshooter)
   — say who owned what.
2. **(1 min)** Show the GitHub repo: `k8s/`, `.github/workflows/`, Dockerfiles, tests.
3. **(1 min)** Trigger a real deploy: push a trivial change, show the Actions run go
   green, pods rolling in `oc get pods -w`.
4. **(1 min)** Hit the Route in a browser — show the working app over HTTPS, log in
   with a seeded demo account.
5. **(2 min)** Load balancing + HPA: run the `hey` load test live, watch `oc get hpa -w`
   and `oc get pods -w` scale up in a split terminal.
6. **(2 min)** Zero-downtime rollout: continuous curl loop in one pane, `oc rollout
   restart` in another — point out zero failed requests.
7. **(1 min)** Security: `oc get secret`, `oc get networkpolicy`, `oc auth can-i` denial
   for the restricted ServiceAccount, TLS padlock on the route URL.
8. **(1 min)** Serverless: `oc get ksvc` showing 0 pods, then fire the reminder job and
   watch a pod appear and disappear — explicitly tie this back to the README's known
   issue you fixed.
9. **(1 min)** Monitoring: OpenShift Observe dashboard with live CPU graph from the
   load test you just ran, plus a log tail.
10. **(1 min)** Close: recap the deliverables checklist against what was just shown.

---

## 12. Deliverables checklist (paste into your submission doc)

- [x] Source in Git (`github.com/ayshrosine/AssetFlow`)
- [x] CI/CD — `.github/workflows/ci-cd.yaml`
- [x] K8s/OpenShift manifests — `k8s/base/*.yaml`
- [x] Image in registry — Quay.io `assetflow-backend`, `assetflow-frontend`
- [x] Serverless — Knative `assetflow-reminder-job` + `PingSource`
- [x] Load balancing — `Service` + `Route`
- [x] HPA — `backend-hpa.yaml`, CPU-based
- [x] HA — 3 replicas, `RollingUpdate` (maxUnavailable:0), `PodDisruptionBudget`
- [x] Security — edge TLS Route, `Secret`, dedicated `ServiceAccount`/`Role`/`RoleBinding`, `NetworkPolicy`
- [x] Probes — liveness/readiness/startup on `/healthz`, `/readyz`, `/startupz`
- [x] Persistent storage — PVC mounted at `/app/uploads`
- [x] Monitoring — OpenShift Observe dashboards + structured logs
- [x] Live demo — scripted above

---

## Open questions to settle before you start building

1. Do you actually have **OpenShift Serverless** and **OpenShift Pipelines** operators
   installed in your specific Sandbox project (not just visible as catalog tiles)? Check
   under **Serverless** / **Pipelines** in the left nav after provisioning — if they're
   not usable, the reminder job can fall back to a plain `CronJob` (still counts as
   "event-driven scheduled workload," just not Knative-scale-to-zero).
2. What's your Sandbox CPU/memory quota (`oc describe quota`)? Size `requests`/`limits`
   and HPA thresholds against it *before* the demo, not during.
3. How long until your Sandbox environment expires relative to your demo date? Sandbox
   environments are time-limited; confirm you can extend/renew, or re-provision with
   enough buffer.
