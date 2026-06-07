# Prompt 5: Integrate Frontend with Backend (End-to-End)

Connect the React frontend to the FastAPI backend. Wire up WebSocket for live progress, auth for all routes, and history display.

## What to build

### API Integration

- When the user clicks "Run Analysis", send `POST /api/analyze` with the selected region and JWT in the `Authorization` header.
- On the backend, validate the JWT on all protected endpoints (`/api/analyze`, `/api/history`, `/api/regions`) using a FastAPI dependency.

### WebSocket Progress

- After triggering analysis, connect to `ws://localhost:8000/ws/progress/{analysis_id}` from React.
- Display each progress message in the `ProgressTracker` component as an animated step list (e.g., querying Cost Explorer, scanning identified active services, running AI evaluations).

### History + Reports

- History page fetches from `GET /api/history` with JWT.
- Clicking a past analysis opens the Report page with full details.

### Report Display

- Summary card at the top: total resources scanned, issues found, estimated  monthly and yearly savings.
- Each issue shows: resource name/ARN, issue type (over-provisioned / unused / misconfigured), severity badge (high = red, medium = yellow, low = green), explanation, and an AWS CLI fix command in a copyable code block.

### Final Testing

- Test the full flow: signup → login → select AWS Region → run cost-explorer discovery analysis → see live progress → view report with CLI fixes → check history.

Refer to `Architecture.MD` and `RequestFlow.MD`. This covers the full end-to-end flow — steps ① through ⑧.
