# Day 43 Performance Notes

## FastAPI Screener Concurrency

Test:
10 concurrent requests to:

`GET /api/v1/screener?min_roe=15&max_de=1&min_fcf=0&min_rev_cagr_5yr=10`

Results:

- Requests: 10
- HTTP 200 responses: 10 / 10
- Expected screener count: 22
- All requests returned count 22
- Total wall time: 1.065 seconds
- Slowest individual request: 1.028 seconds
- Requirement: all requests within 10 seconds
- Result: PASS

## Company Profile Performance

| Company | HTTP Status | Response Time |
|---|---:|---:|
| TCS | 200 | 0.018 s |
| HDFCBANK | 200 | 0.019 s |
| RELIANCE | 200 | 0.007 s |
| SUNPHARMA | 200 | 0.008 s |
| TATASTEEL | 200 | 0.032 s |

- Slowest response: 0.032 seconds
- Requirement: less than 3 seconds
- Result: PASS

## Concurrent Application Runtime

FastAPI:
- Port: 8000
- Health endpoint returned HTTP 200

Streamlit:
- Port: 8501
- Dashboard returned HTTP 200

Both services were running simultaneously.

## Day 43 Status

- 10 concurrent screener calls under 10 seconds: PASS
- Five company profiles under 3 seconds: PASS
- FastAPI and Streamlit simultaneous runtime: PASS

Overall Day 43 result: PASS
