# NotifyIQ — REST API Reference

The NotifyIQ backend exposes a local FastAPI service (default bound to `http://127.0.0.1:8000`).

## Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health, model status, and DB readiness |
| `POST` | `/notifications/import` | Validate and import a batch of Android notification events |
| `POST` | `/notifications/process` | Process a single notification event through AI pipeline |
| `GET` | `/notifications` | Paginated notification list with filters |
| `GET` | `/notifications/{id}` | Detailed notification record with explanations |
| `DELETE` | `/notifications/{id}` | Delete notification and its cascade |
| `GET` | `/actions` | List detected action items |
| `GET` | `/actions/upcoming` | List actions with upcoming deadlines |
| `PATCH` | `/actions/{id}` | Update action status (`open`, `completed`, `dismissed`) |
| `POST` | `/feedback` | Submit user correction on classification or priority |
| `GET` | `/feedback` | List historical user feedback |
| `GET` | `/analytics/summary` | Aggregate statistics (total, high priority, actions, etc.) |
| `GET` | `/analytics/categories` | Counts and average confidence by category |
| `GET` | `/analytics/priorities` | Counts and average score by priority level |
| `GET` | `/settings` | Retrieve application settings |
| `PATCH` | `/settings` | Update validated configuration settings |
| `POST` | `/privacy/purge` | Purge all stored notifications, actions, and feedback |

## Example: Import Notification Batch

`POST /notifications/import`

```json
{
  "notifications": [
    {
      "schema_version": 1,
      "event_id": "evt-android-001",
      "package_name": "com.university.portal",
      "title": "Assignment Deadline",
      "text": "Please submit your capstone report before tomorrow 5 PM.",
      "posted_at": "2026-10-19T10:00:00Z",
      "event_type": "posted"
    }
  ]
}
```

Response:
```json
{
  "total_records": 1,
  "accepted_count": 1,
  "rejected_count": 0,
  "already_processed_count": 0,
  "accepted_records": [...],
  "rejected_records": [],
  "warnings": []
}
```

## Running the API

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.
