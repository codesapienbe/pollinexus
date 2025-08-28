# Visualizations API

## Create

- `POST /visualizations/bee-distribution/`
- `POST /visualizations/seasonal-patterns/`
- `POST /visualizations/site-comparison/`
- `POST /visualizations/dashboard/`
- `POST /visualizations/batch/`

## Manage

- `GET /visualizations/{visualization_id}/status?task_id=...`
- `GET /visualizations/{visualization_id}/download?task_id=...`
- `DELETE /visualizations/{visualization_id}?task_id=...`
- `GET /visualizations/available-types`

## Example

```bash
curl -X POST "http://localhost:8000/api/v1/visualizations/bee-distribution/?dataset_id=1" \
  -H "Content-Type: application/json" \
  -d '{"top_n": 20, "include_percentages": true}'
```

## Presentation Notes
>>
>> Use visuals to validate analysis narratives: distribution → seasonal → site comparison.
>> Show async flow mirrored to analysis; emphasize reproducible artifacts (downloadable files).
