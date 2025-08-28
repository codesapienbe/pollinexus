# Dataset Management API

## Endpoints

- `POST /datasets/` — Upload dataset (CSV/Excel/Parquet)
- `GET /datasets/` — List datasets (pagination + search)
- `GET /datasets/{id}` — Get dataset by id
- `PUT /datasets/{id}` — Update dataset
- `DELETE /datasets/{id}` — Delete dataset
- `GET /datasets/{id}/info` — Dataset statistics and file info
- `POST /datasets/search` — Search datasets
- `GET /datasets/{id}/health` — Dataset health & validation status

## Parameters

- List: `skip`, `limit`, `search`

## Examples

Upload:

```bash
curl -X POST "http://localhost:8000/api/v1/datasets/" \
  -F "name=Plants and Bees Dataset" \
  -F "description=Sample pollinator data" \
  -F "file=@plants_and_bees.csv"
```

List:

```bash
curl "http://localhost:8000/api/v1/datasets/?skip=0&limit=20&search=pollinator"
```

## Presentation Notes
>>
>> Motivate with data quality: checksum, validation, and schema inference to prevent garbage-in.
>> Show `info` for stats (records, columns, dtypes, nulls) then `health` to validate file integrity.
>> Mention privacy: avoid logging file contents or sensitive metadata.
