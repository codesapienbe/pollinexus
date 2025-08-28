# File Checksum Implementation for Duplicate Detection

## Overview

This implementation adds SHA-256 checksum validation to the dataset upload process to prevent duplicate file uploads. The system calculates a unique hash for each uploaded file and stores it in the database for efficient duplicate detection.

## Key Features

### 1. SHA-256 Checksum Calculation
- **Algorithm**: SHA-256 (64-character hexadecimal hash)
- **Efficiency**: Chunked reading (4KB chunks) for large files
- **Reliability**: Handles file I/O errors gracefully

### 2. Database Schema Changes
- **New Column**: `file_checksum VARCHAR(64)` in `datasets` table
- **Index**: `idx_datasets_checksum` for fast duplicate lookups
- **Migration**: Automatic migration for existing datasets

### 3. Duplicate Detection
- **Pre-upload Check**: Validates checksum before saving file
- **Database Lookup**: Efficient index-based duplicate detection
- **Error Handling**: Returns 409 Conflict for duplicate files

## Implementation Details

### Database Model Updates

```python
class Dataset(Base):
    # ... existing fields ...
    file_checksum = Column(String(64), nullable=False, index=True)
    
    __table_args__ = (
        # ... existing indexes ...
        Index('idx_datasets_checksum', 'file_checksum'),
    )
```

### Request Model Validation

```python
class DatasetCreate(BaseModel):
    # ... existing fields ...
    file_checksum: str = Field(..., min_length=64, max_length=64)
    
    @validator('file_checksum')
    def validate_checksum(cls, v):
        if not v or len(v) != 64:
            raise ValueError('File checksum must be a 64-character SHA-256 hash')
        try:
            int(v, 16)  # Validate hex format
        except ValueError:
            raise ValueError('File checksum must be a valid hexadecimal string')
        return v.lower()
```

### Upload Process Flow

1. **File Validation**: Check file type and size
2. **Checksum Calculation**: Calculate SHA-256 hash of uploaded file
3. **Duplicate Check**: Query database for existing checksum
4. **File Save**: Save file if no duplicate found
5. **Database Record**: Create dataset record with checksum

### Security Features

- **Input Validation**: Strict checksum format validation
- **Error Handling**: Comprehensive error logging and sanitization
- **File Cleanup**: Automatic cleanup on validation failures
- **Audit Trail**: Full logging of checksum operations

## API Endpoint Changes

### POST /api/v1/datasets/

**Enhanced Response Codes:**
- `200 OK`: File uploaded successfully
- `400 Bad Request`: Invalid file type or checksum calculation error
- `409 Conflict`: Duplicate file detected
- `500 Internal Server Error`: Unexpected errors

**Response Example (Duplicate):**
```json
{
  "detail": "File already exists as dataset 'plants_and_bees' (ID: 1)"
}
```

## Migration Process

### Automatic Migration
The system automatically:
1. Detects missing `file_checksum` column
2. Adds column and index to existing database
3. Calculates checksums for existing files
4. Handles missing files gracefully

### Migration Logging
```
INFO: Adding file_checksum column to datasets table
INFO: Calculated checksum for dataset 1: a1b2c3d4...
WARNING: File not found for dataset 2: /path/to/missing/file.csv
ERROR: Failed to calculate checksum for dataset 3: Permission denied
```

## Performance Considerations

### Optimizations
- **Chunked Reading**: 4KB chunks for memory efficiency
- **Database Index**: Fast duplicate lookups
- **Early Validation**: Check before file save
- **Connection Pooling**: Efficient database connections

### Monitoring
- **Performance Metrics**: Checksum calculation timing
- **Error Tracking**: Failed checksum calculations
- **Duplicate Detection**: Rate of duplicate uploads

## Testing

### Test Script
Run `python test_checksum.py` to verify functionality:
- Validates checksum format (64-character hex)
- Tests duplicate detection
- Verifies file I/O handling

### Manual Testing
1. Upload a file and note the checksum
2. Attempt to upload the same file again
3. Verify 409 Conflict response
4. Check database for single record

## Error Handling

### Common Scenarios
1. **File Not Found**: Sets checksum to 'FILE_NOT_FOUND'
2. **Permission Error**: Sets checksum to 'CALCULATION_ERROR'
3. **Invalid Format**: Returns 400 Bad Request
4. **Database Error**: Returns 500 Internal Server Error

### Logging
All checksum operations are logged with:
- Request ID and correlation ID
- File name and checksum
- Operation timing
- Error details (if applicable)

## Security Considerations

### Data Protection
- **No PII in Checksums**: Checksums don't contain sensitive data
- **Input Sanitization**: Strict validation of checksum format
- **Error Information**: Limited error details in responses

### Audit Trail
- **Complete Logging**: All checksum operations logged
- **Request Tracking**: Correlation IDs for traceability
- **Performance Monitoring**: Timing and error metrics

## Future Enhancements

### Potential Improvements
1. **Multiple Hash Algorithms**: Support for MD5, SHA-1
2. **Incremental Updates**: Checksum updates for modified files
3. **Batch Processing**: Bulk checksum calculation
4. **Cloud Storage**: Checksum validation for cloud files

### Monitoring Enhancements
1. **Duplicate Rate Metrics**: Track duplicate upload patterns
2. **Performance Alerts**: Slow checksum calculations
3. **Storage Analytics**: Checksum-based storage optimization

## Conclusion

This implementation provides robust duplicate detection while maintaining security and performance. The SHA-256 checksum ensures data integrity and prevents storage waste from duplicate uploads. 