# Health & Information API

- Base URL: `http://localhost:8000/api/v1`
- Interactive Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints
- `GET /api/v1/` — Root
- `GET /api/v1/info` — API information and capabilities
- `GET /api/v1/health` — Quick health check
- `GET /api/v1/health/detailed` — Comprehensive health status
- `GET /api/v1/security/status` — Security monitoring status
- `GET /api/v1/metrics` — System metrics

## Examples
```bash
curl "http://localhost:8000/api/v1/health"
```

```bash
curl "http://localhost:8000/api/v1/info"
```

## Presentation Notes
>> Start any demo with `health` to show uptime, then `info` to outline capabilities and versions.
>> Tie metrics/health to observability: demonstrate quick diagnosis before deeper API flows. 