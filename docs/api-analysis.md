# Data Analysis API

## Start Analyses
- `POST /analysis/bee-preferences/` — Body: `dataset_id`, `target_column`, `model_type`, `test_size`
- `POST /analysis/plant-recommendations/` — Body: `dataset_id`, `top_n`, `criteria[]`
- `POST /analysis/seasonal/` — Query: `dataset_id`; Body: `include_trends`, `seasonal_periods`
- `POST /analysis/site-comparison/` — Query: `dataset_id`; Body: `metrics[]`, `group_by`

## Jobs
- `GET /analysis/jobs/` — Filters: `dataset_id`, `status`, `skip`, `limit`
- `GET /analysis/jobs/{id}` — Job metadata
- `GET /analysis/jobs/{id}/results` — Results
- `GET /analysis/jobs/{id}/status` — Detailed status (Celery)
- `DELETE /analysis/jobs/{id}` — Cancel job
- `GET /analysis/stats` — Statistics summary

## Example
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/bee-preferences/" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "target_column": "nonnative_bee", "model_type": "random_forest", "test_size": 0.2}'
```

## Presentation Notes
>> Frame the goal: translate ecological questions into ML tasks; highlight target, features, and evaluation.
>> Explain async design: Celery for long-running jobs; poll `status` then fetch `results`.
>> Interpretability: feature importance drives recommendations; avoid overclaiming beyond metrics. 