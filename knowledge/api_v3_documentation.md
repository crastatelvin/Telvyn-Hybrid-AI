# Aetherial API v3: Public Documentation

## Authentication
- **Method:** Bearer Token (JWT).
- **Header:** `Authorization: Bearer <token>`

## Endpoints
### GET /v3/satellites
- Returns list of active satellites.
- Rate Limit: 100 req/min.

### POST /v3/telemetry
- Push raw telemetry data.
- Payload: JSON (Max 5MB).
