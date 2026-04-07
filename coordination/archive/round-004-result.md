# Current Round Result

## Round
Round 004 - Simulation Pose Ingress HTTP Bridge

## Summary

- Status: PASSED
- The in-process simulation pose-ingress runtime is now exposed through a lightweight FastAPI bridge.
- An external process can start the sim runtime, post pose payloads, finish the stream, and inspect state/session over HTTP.
- Manual HTTP validation triggered real tour narration through the sim path without changing `core`.

## What I Changed

- Added a thin HTTP bridge app in `services/sim_pose_ingress/app.py`.
  - wraps the existing `SimPoseIngressRuntime`
  - does not add a second orchestrator or transport-specific business layer
- Added a server startup script:
  - `scripts/run_sim_pose_ingress_server.py`
- Added a demo client script that posts the existing sim pose stream over HTTP:
  - `scripts/post_sim_pose_stream.py`
- Added HTTP bridge documentation:
  - `docs/SIM_POSE_HTTP_BRIDGE.md`
- Updated the existing sim pose-ingress contract doc to point at the HTTP bridge:
  - `docs/SIM_POSE_INGRESS_CONTRACT.md`
- Added endpoint-level automated tests:
  - `tests/test_sim_pose_http_bridge.py`

## Exact Files Changed

- `services/sim_pose_ingress/app.py`
- `scripts/run_sim_pose_ingress_server.py`
- `scripts/post_sim_pose_stream.py`
- `docs/SIM_POSE_HTTP_BRIDGE.md`
- `docs/SIM_POSE_INGRESS_CONTRACT.md`
- `tests/test_sim_pose_http_bridge.py`
- `coordination/latest_result.md`

## Exact HTTP Endpoints Added

- `GET /health`
- `POST /runtime/start`
- `POST /poses`
- `POST /poses/batch`
- `POST /stream/finish`
- `GET /state`
- `GET /session/latest`

## Exact HTTP Payloads Used For Validation

### Start Runtime

Endpoint:

```text
POST /runtime/start
```

Request body:

```json
{}
```

### Single Pose

Endpoint:

```text
POST /poses
```

Request body:

```json
{
  "x": -0.6,
  "y": 0.0,
  "label": "gate_trigger_edge"
}
```

### Batch Pose Upload

Endpoint:

```text
POST /poses/batch
```

Request body used in manual validation:

```json
{
  "poses": [
    {
      "x": -1.8,
      "y": -0.7,
      "label": "gate_approach"
    },
    {
      "x": -0.6,
      "y": 0.0,
      "label": "gate_trigger_edge"
    },
    {
      "x": 0.0,
      "y": 0.0,
      "label": "gate_inside"
    },
    {
      "x": 1.3,
      "y": 0.1,
      "label": "gate_depart"
    },
    {
      "x": 3.9,
      "y": 0.8,
      "label": "plaza_trigger_edge"
    },
    {
      "x": 5.0,
      "y": 1.0,
      "label": "plaza_inside"
    }
  ]
}
```

### Finish Stream

Endpoint:

```text
POST /stream/finish
```

Request body:

```json
{}
```

## Exact Validation Performed

### Automated

- `python -m unittest tests.test_sim_pose_http_bridge -v`
  - passed
  - `Ran 3 tests ... OK`
- `python -m unittest discover -s tests`
  - passed
  - `Ran 24 tests ... OK`

### Manual HTTP Validation

Server:

```shell
python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml --host 127.0.0.1 --port 8100
```

Client:

```shell
python scripts/post_sim_pose_stream.py --base-url http://127.0.0.1:8100
```

Also validated directly with explicit HTTP requests against:
- `/health`
- `/runtime/start`
- `/poses/batch`
- `/stream/finish`
- `/state`
- `/session/latest`

### Observed HTTP Validation Results

`GET /health` returned:

```json
{
  "status": "ok",
  "service": "sim-pose-ingress-runtime",
  "env_name": "sim",
  "pose_provider_type": "sim_ingress",
  "narrator_type": "mock",
  "ingress_contract": {
    "required_fields": ["x", "y"],
    "optional_fields": ["label"]
  }
}
```

`POST /runtime/start` returned a running tour state with:
- `active_spot_id: "gate"`
- `state: "NAVIGATING"`

`POST /poses/batch` returned:

```json
{
  "ok": true,
  "action": "ingest_pose_batch",
  "accepted_count": 6
}
```

`GET /state` after finish showed externally ingested progress through the route and included:

```text
last_narration_text = "This central plaza is the mid-route checkpoint in the demo tour. It helps us verify that state transitions and narration continue cleanly after the first stop."
```

`GET /session/latest` returned a recorded session with:
- `event_count: 21`
- non-null `latest_narration_text`
- a real log path under `session_logs/sim/`

### Narration Trigger Confirmed Through HTTP Path

At least one POI trigger and narration occurred through the HTTP-driven sim path.

Observed narration through the bridge:

```text
Welcome to the East Gate. This first stop introduces the route and confirms that the guided tour can trigger narration as soon as the robot reaches a POI.
```

And later:

```text
This central plaza is the mid-route checkpoint in the demo tour. It helps us verify that state transitions and narration continue cleanly after the first stop.
```

## How This Relates To The Existing In-Process Sim Runtime

- `services/sim_pose_ingress/runtime.py` remains the in-process baseline seam
- `services/sim_pose_ingress/app.py` is only a transport wrapper over that runtime
- simulator transport logic remains outside `core`
- the mock API path remains untouched

## What Still Remains Before Real Isaac Sim Integration

- a real simulator-side publisher process or Isaac bridge
- coordinate-frame conversion between Isaac Sim output and the tour map frame
- timestamp semantics if replay fidelity matters
- longer-lived reconnect and session lifecycle handling
- any production hardening beyond this minimal machine-to-machine bridge

## Current Branch

- `main`

## Full Git Status --short --branch

```text
## main...origin/main [ahead 5]
 M docs/DEV_WORKFLOW.md
?? coordination/
```

## Commit Hash

- `7ab6a98402cfc0692f0987dbde179523a84aba3d`

## Staged / Committed State

- Work for this round: committed
- `coordination/latest_result.md`: updated locally, not staged
- Unrelated local modification still exists in `docs/DEV_WORKFLOW.md` and was intentionally left untouched

## Blockers, Risks, Or Remaining Gaps

- The bridge is intentionally minimal and not hardened for production transport.
- It uses request/response HTTP only; there is no streaming transport or backpressure behavior yet.
- It proves process-boundary transport, but not direct Isaac SDK hookup.
