# API Contracts

## User-Facing Interface

### Submit Research Request

```
POST /research
Request:  { topic, domain_tags?, constraints? }
Response: { request_id, status: "pending" }
```

### View Intermediate Findings

```
GET /research/{request_id}/findings
Response: { findings: { agent_role: [Finding, ...] } }
```

### Submit Steering Instruction

```
POST /research/{request_id}/steer
Request:  { instruction_text, target_agents }
Response: { request_id, applied: true }
```

### Get Synthesis Report

```
GET /research/{request_id}/report
Response: { report: SynthesisReport }
```

## Operations-Facing Interface

### Get Telemetry

```
GET /telemetry?window=100
Response: { events: [TelemetryEvent, ...], summary: { ... } }
```

### Get Workflow Status

```
GET /research/{request_id}/status
Response: { request_id, status, agents: { role: execution_state }, timeline: [...] }
```

### Intervene in Workflow

```
POST /research/{request_id}/intervene
Request:  { action: "resume"|"restart"|"abort", agent_role? }
Response: { request_id, status: after_action }
```
