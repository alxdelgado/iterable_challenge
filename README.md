# Iterable Integration Challenge - Phase 3: Python Integration

## Project Overview

This project implements a complete data pipeline that:
1. **Phase 1**: Creates a SQL database with Customers and Page_views tables
2. **Phase 2**: Queries pro plan users who recently viewed pricing/settings pages
3. **Phase 3**: Sends user profile updates and page view events to Iterable via API

## Architecture

### Module Structure

```
├── database_setup.sql          # Phase 1: Database schema and seed data
├── phase2_queries.sql          # Phase 2: Three query approaches
├── .env.example                # Environment variables template
├── db_connection.py            # Database connection and query execution
├── iterable_client.py          # Iterable API client (users/update, events/track)
├── logger_config.py            # Logging configuration
├── main.py                     # Main integration orchestrator
└── README.md                   # This file
```

### Data Flow

```
Database Query → Result Set → For Each User:
                                ├─ POST /api/users/update (profile data)
                                └─ POST /api/events/track (page view event)
```

## Phase 3: Python Integration

### Requirements Implemented

✅ **Database Connection**
- Connects to MySQL database using credentials from .env
- Executes Phase 2 Query 2 (CTE + window functions)
- Handles connection errors gracefully

✅ **Iterable API Integration**
- **POST /api/users/update**: Updates user profiles with:
  - `first_name`, `last_name`, `plan_type`
  - `recent_page_view` (boolean: true)
  - `candidate` (string identifier)
- **POST /api/events/track**: Tracks page_view events with:
  - `page`, `device` (browser), `location`
  - `timestamp`, `candidate`

✅ **Error Handling**
- Distinguishes 4xx client errors (BadParams, AuthFailed) from 5xx server errors
- Logs all failures with request/response details
- Supports graceful degradation (partial failures don't stop processing)

✅ **Logging**
- Console output: Real-time feedback (INFO level)
- File logging: Detailed audit trail (DEBUG level)
- Rotating file handler: Prevents log files from growing too large
- Timestamps on all entries

✅ **Configuration**
- Uses .env file for credentials (no hardcoding)
- Support for custom log levels and file paths
- Clean separation of concerns

✅ **Code Quality**
- Modular design: Separate modules for database, API, logging
- Type hints for all function parameters and returns
- Comprehensive docstrings
- Error handling with try-except blocks

## Setup Instructions

### 1. Install Dependencies

```bash
pip install python-dotenv mysql-connector-python requests
```

### 2. Configure Environment

Copy the example file and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your database and API credentials:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=iterable_challenge
ITERABLE_API_KEY=your_api_key_here
ITERABLE_API_BASE_URL=https://api.iterable.com
LOG_LEVEL=INFO
LOG_FILE=iterable_integration.log
```

### 3. Initialize Database

Run the Phase 1 database setup:

```bash
mysql -u root -p < database_setup.sql
```

### 4. Run Integration

```bash
python main.py
```

## Usage Examples

### Basic Execution

```bash
python main.py
```

This will:
1. Load .env configuration
2. Connect to the database
3. Query pro users with recent engagement (last 7 days, pricing/settings pages)
4. For each user, call both Iterable endpoints
5. Generate summary report and detailed JSON results

### Check Logs

Real-time console output:
```
2026-01-13 14:30:45 - __main__ - INFO - Starting Iterable Integration - Phase 3
2026-01-13 14:30:45 - __main__ - INFO - [STEP 1] Loading environment variables...
2026-01-13 14:30:45 - db_connection - INFO - Successfully connected to database: iterable_challenge
...
```

File-based logs: `iterable_integration.log` (debug-level details)

Detailed results: `integration_results_20260113_143045.json` (timestamped)

## Database Schema

### Customers Table

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key, auto-increment |
| email | TEXT | Unique identifier |
| first_name | TEXT | User first name |
| last_name | TEXT | User last name |
| plan_type | TEXT | free, basic, pro, enterprise |
| candidate | TEXT | yes/no identifier |

### Page_views Table

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key, auto-increment |
| user_id | INTEGER | FK to customers(id) |
| page | TEXT | pricing, settings, features, home, blog |
| device | TEXT | mobile, desktop, tablet |
| browser | TEXT | Chrome, Firefox, Safari, Edge |
| location | TEXT | City, State |
| event_time | TIMESTAMP | Event occurrence time |

## Phase 2 Query 2 (Used in Python)

The main query uses a CTE with window functions to get the latest page view per pro user:

```sql
WITH ranked_views AS (
    SELECT 
        c.id, c.email, c.first_name, c.last_name, c.plan_type, c.candidate,
        pv.page, pv.device, pv.browser, pv.location, pv.event_time,
        ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY pv.event_time DESC) as view_rank
    FROM customers c
    INNER JOIN page_views pv ON c.id = pv.user_id
    WHERE c.plan_type = 'pro'
        AND pv.page IN ('pricing', 'settings')
        AND pv.event_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
)
SELECT * FROM ranked_views WHERE view_rank = 1
```

**Key Concepts:**
- **CTE (WITH clause)**: Stages window function results before filtering
- **ROW_NUMBER()**: Assigns sequential integers within each customer partition
- **PARTITION BY c.id**: Ranks rows per customer independently
- **ORDER BY pv.event_time DESC**: Latest timestamp gets rank 1
- **WHERE view_rank = 1**: Filters to only latest per customer

## Iterable API Endpoints

### users/update

**Endpoint:** `POST /api/users/update`

**Request:**
```json
{
  "email": "user@example.com",
  "dataFields": {
    "first_name": "John",
    "last_name": "Doe",
    "plan_type": "pro",
    "recent_page_view": true,
    "candidate": "yes"
  }
}
```

**Response:**
```json
{
  "code": "Success",
  "msg": "User updated",
  "params": {}
}
```

**Rate Limit:** 500 requests/second per project

**Error Codes:**
- `BadApiKey`: Invalid API key
- `BadJsonBody`: Malformed JSON
- `BadParams`: Invalid parameters
- `Success`: Operation succeeded

### events/track

**Endpoint:** `POST /api/events/track`

**Request:**
```json
{
  "email": "user@example.com",
  "eventName": "page_view",
  "dataFields": {
    "page": "pricing",
    "device": "desktop",
    "location": "San Francisco, CA",
    "timestamp": "2026-01-13 14:30:45",
    "candidate": "yes"
  }
}
```

**Response:**
```json
{
  "code": "Success",
  "msg": "Event tracked",
  "params": {}
}
```

**Rate Limit:** 2000 requests/second per project

**Authentication:** Both endpoints use API key in headers:
```
Api-Key: your_api_key_here
Content-Type: application/json
```

## Error Handling

The system distinguishes between three failure modes:

### 4xx Client Errors (Bad Request)
- HTTP 400, 401, 409, etc.
- Indicates problem with request (invalid params, auth failure)
- Logged as error with full request/response
- Processing continues to next record

Example:
```
2026-01-13 14:31:22 - iterable_client - ERROR - 4xx Client Error from users/update: Status 400
Response: {'code': 'BadParams', 'msg': 'Invalid parameter: plan_type'}
```

### 5xx Server Errors (Internal Server Error)
- HTTP 500, 502, 503, etc.
- Indicates Iterable service issue
- Logged as error
- Could implement retry logic here

Example:
```
2026-01-13 14:31:25 - iterable_client - ERROR - 5xx Server Error from events/track: Status 502
Response: {'code': 'DatabaseError', 'msg': 'Backend service unavailable'}
```

### API Response Codes
- `Success`: Operation completed
- Any other code: Logged as warning/error with message

## Logging Output Example

```
2026-01-13 14:30:45 - __main__ - INFO - ======================================================================
2026-01-13 14:30:45 - __main__ - INFO - Starting Iterable Integration - Phase 3
2026-01-13 14:30:45 - __main__ - INFO - ======================================================================

2026-01-13 14:30:45 - __main__ - INFO - [STEP 1] Loading environment variables...
2026-01-13 14:30:45 - __main__ - INFO - Environment variables loaded successfully

2026-01-13 14:30:45 - __main__ - INFO - [STEP 2] Connecting to database...
2026-01-13 14:30:45 - db_connection - INFO - Successfully connected to database: iterable_challenge

2026-01-13 14:30:45 - __main__ - INFO - [STEP 3] Executing Phase 2 Query 2...
2026-01-13 14:30:45 - db_connection - INFO - Query executed successfully, returned 3 rows

2026-01-13 14:30:45 - __main__ - INFO - Found 3 pro user(s) with recent engagement

2026-01-13 14:30:45 - __main__ - INFO - [STEP 4] Initializing Iterable API client...
2026-01-13 14:30:45 - __main__ - INFO - Iterable API client initialized

2026-01-13 14:30:45 - __main__ - INFO - [STEP 5] Processing user records...
2026-01-13 14:30:45 - __main__ - INFO - Processing record 1/3
2026-01-13 14:30:45 - iterable_client - INFO - Processing user: sarah.johnson@email.com
2026-01-13 14:30:46 - iterable_client - INFO - users/update call successful: Success
2026-01-13 14:30:47 - iterable_client - INFO - events/track call successful: Success
2026-01-13 14:30:47 - iterable_client - INFO - ✓ Successfully processed user: sarah.johnson@email.com

...

2026-01-13 14:30:49 - __main__ - INFO - ======================================================================
2026-01-13 14:30:49 - __main__ - INFO - INTEGRATION SUMMARY
2026-01-13 14:30:49 - __main__ - INFO - ======================================================================
2026-01-13 14:30:49 - __main__ - INFO - Total users processed: 3
2026-01-13 14:30:49 - __main__ - INFO - ✓ Successful (both API calls): 3
2026-01-13 14:30:49 - __main__ - INFO - ⚠ Partial failures (one call failed): 0
2026-01-13 14:30:49 - __main__ - INFO - ✗ Total failures (both calls failed): 0
2026-01-13 14:30:49 - __main__ - INFO - ======================================================================
```

## Results File

The script generates a timestamped JSON file with detailed results:

```json
{
  "total_users": 3,
  "successful": 3,
  "partial_failures": 0,
  "total_failures": 0,
  "records": [
    {
      "email": "sarah.johnson@email.com",
      "timestamp": "2026-01-13T14:30:46.123456",
      "users_update": {
        "success": true,
        "response": {
          "code": "Success",
          "msg": "User updated",
          "params": {}
        }
      },
      "events_track": {
        "success": true,
        "response": {
          "code": "Success",
          "msg": "Event tracked",
          "params": {}
        }
      },
      "overall_success": true
    },
    ...
  ]
}
```

## Troubleshooting

### Database Connection Failed

**Problem:** `Error connecting to database`

**Solution:**
1. Verify MySQL is running: `mysql -u root -p`
2. Check credentials in .env file
3. Ensure database exists: `CREATE DATABASE iterable_challenge;`
4. Run Phase 1 setup: `mysql -u root -p < database_setup.sql`

### Missing Environment Variables

**Problem:** `Missing required environment variables: DB_PASSWORD, ITERABLE_API_KEY`

**Solution:**
1. Ensure .env file exists in project root
2. Add all required variables (see .env.example)
3. No spaces around `=` in .env file

### No Users Found

**Problem:** `No pro users with recent pricing/settings page views found`

**Solution:**
1. Verify data was inserted: `SELECT COUNT(*) FROM customers WHERE plan_type='pro';`
2. Check date filtering: Events must be within last 7 days and on pricing/settings pages
3. Run Phase 1 setup again to ensure fresh data

### Iterable API Errors

**Problem:** 4xx or 5xx responses from Iterable

**Solution:**
1. Verify API key is correct in .env file
2. Check endpoint URLs in logs
3. Review error response code and message
4. See "Error Handling" section above

## Advanced Configuration

### Custom Log Level

In .env:
```env
LOG_LEVEL=DEBUG  # Shows all operations including API payloads
```

### Custom Log File

In .env:
```env
LOG_FILE=/var/log/iterable_integration.log
```

### Custom API Base URL

In .env:
```env
ITERABLE_API_BASE_URL=https://api-staging.iterable.com  # For testing
```

## Performance Considerations

- **Rate Limits**: 500 req/sec for users/update, 2000 req/sec for events/track
- **Batch Processing**: Current implementation processes one user at a time
- **Timeout**: 10-second timeout per API call
- **Retry Logic**: Not implemented (can be added in IterableClient)

## Future Enhancements

1. **Batch API Calls**: Group multiple users into single requests if Iterable supports
2. **Retry Logic**: Implement exponential backoff for 5xx errors
3. **Rate Limit Management**: Track and respect per-second rate limits
4. **Incremental Processing**: Track processed users to resume on failure
5. **Webhook Verification**: Confirm events received by Iterable
6. **Data Validation**: Pre-validate data before sending to API

## Security Notes

- Never commit .env file with real credentials
- Use API keys with minimal required permissions
- Rotate API keys regularly
- Store logs securely (they may contain PII)
- Use HTTPS for all API calls (default)

## Summary of Concepts

### Window Functions (Phase 2)
- `ROW_NUMBER()`: Sequential ranking within partitions
- `PARTITION BY`: Independent groups for calculation
- `ORDER BY`: Determines ranking order
- Preserves individual rows (unlike GROUP BY)

### CTEs (Common Table Expressions)
- Named temporary result set using WITH clause
- Can be referenced in main query
- Allows complex logic in stages
- Improves readability

### API Integration Patterns
- Request/Response structure consistency
- HTTP status codes vs API response codes
- Error code categorization (4xx vs 5xx)
- Rate limiting considerations
- Idempotent design (safe to retry)

## Support and Troubleshooting

For issues:
1. Check console output for error messages
2. Review `iterable_integration.log` for detailed logs
3. Check `integration_results_*.json` for API responses
4. Verify environment variables in .env
5. Test database connection independently
6. Test Iterable API key with curl/Postman

---

**Project Status**: ✅ Phase 1 (Database) ✅ Phase 2 (SQL Queries) ✅ Phase 3 (Python Integration)

**Next Step**: Create PDF documentation for project presentation
