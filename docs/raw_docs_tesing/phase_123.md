# Testing Guide - Phase 1, 2 & 3

This document covers how to test all Phase 1, 2, and 3 functionality from both **Backend** (curl/API) and **Frontend** (browser) perspectives.

---

## Prerequisites

- Backend running: `cd services/api && uvicorn app.main:app --reload` (port 8000)
- Frontend running: `cd apps/web && npm run dev` (port 3000)
- Database: Neon PostgreSQL connected
- Redis: Upstash connected

---

## Phase 1 - Database Foundation

### Backend Test: Database Connection

```bash
# Health check (verifies DB connected)
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"api"}
```

**Frontend Test**: 
- Frontend loads without errors
- No database connection errors in console

---

## Phase 2 - Authentication

### Backend Test (curl)

#### 1. Public endpoints work without token
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"api"}

curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok","service":"api"}
```

#### 2. Protected endpoints return 401 without token
```bash
curl http://localhost:8000/api/v1/contracts/
# Expected: 401 Unauthorized

curl -X POST http://localhost:8000/api/v1/upload/ \
  -H "Content-Type: application/json" \
  -d '{"file_url":"test.pdf","original_filename":"test.pdf","file_type":"pdf","file_size_bytes":100}'
# Expected: 401 Unauthorized
```

#### 3. Get JWT from frontend
1. Open http://localhost:3000 in browser
2. Sign in with Clerk
3. Open DevTools (F12) → Application → Local Storage → `__session`
4. Copy the token value

#### 4. Test protected endpoint with valid JWT
```bash
# Replace YOUR_JWT with actual token
curl http://localhost:8000/api/v1/contracts/ \
  -H "Authorization: Bearer YOUR_JWT"
# Expected: {"message":"Success","user_id":"user_...","contracts":[...]}
```

#### 5. Test webhook (user creation)
- Sign up on frontend
- Check backend logs for: `POST /api/v1/webhooks/clerk HTTP/1.1" 200 OK`

---

### Frontend Test

#### 1. Sign Up
1. Go to http://localhost:3000
2. Click Sign Up
3. Enter email (use @clerk.dev for testing)
4. Complete verification

**Verify**: Check backend - user should appear in database
```bash
# Backend should log: INSERT INTO users ...
```

#### 2. Sign In
1. Go to http://localhost:3000/sign-in
2. Enter credentials
3. Redirected to dashboard

**Verify**: JWT stored in browser Local Storage (`__session`)

#### 3. Protected pages work when signed in
- Dashboard: http://localhost:3000/dashboard ✅
- Upload: http://localhost:3000/upload ✅

#### 4. Redirect when signed out
1. Sign out from frontend
2. Try to access http://localhost:3000/dashboard
3. Should redirect to /sign-in

---

## Phase 3 - File Upload Pipeline

### Backend Test (curl)

#### 1. Upload without token (should fail)
```bash
curl -X POST http://localhost:8000/api/v1/upload/ \
  -H "Content-Type: application/json" \
  -d '{"file_url":"https://example.com/test.pdf","original_filename":"test.pdf","file_type":"pdf","file_size_bytes":50000}'
# Expected: 401 Unauthorized
```

#### 2. Upload with valid JWT (creates records)
```bash
# Get fresh JWT from frontend first!
curl -X POST http://localhost:8000/api/v1/upload/ \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"file_url":"https://example.com/test.pdf","original_filename":"test.pdf","file_type":"pdf","file_size_bytes":50000}'
# Expected: {"job_id":"...","contract_id":"...","status":"queued","progress_pct":0.0}
```

**Verify in database:**
- Contract created in `contracts` table
- ScanJob created in `scan_jobs` table with status "queued"

#### 3. Get contracts for user
```bash
curl http://localhost:8000/api/v1/contracts/ \
  -H "Authorization: Bearer YOUR_JWT"
# Expected: {"contracts":[{"id":"...","original_filename":"test.pdf",...}]}
```

#### 4. Get scan status
```bash
curl http://localhost:8000/api/v1/scan/YOUR_JOB_ID \
  -H "Authorization: Bearer YOUR_JWT"
# Expected: {"status":"not_implemented","job_id":"..."}
```

---

### Frontend Test

#### 1. Dashboard shows contracts
1. Go to http://localhost:3000/dashboard
2. Should see uploaded contracts
3. Should show "Upload Contract" button

**If empty**: Upload a file first!

#### 2. Sidebar shows recent contracts
1. Go to http://localhost:3000/dashboard
2. Sidebar on left should show recent contracts

#### 3. Upload a new contract
1. Go to http://localhost:3000/upload
2. Drop or select a file
3. Click upload
4. Wait for processing
5. Click "View Analysis"

**Verify:**
- Backend creates Contract + ScanJob
- Dashboard updates with new contract
- Sidebar shows new contract

#### 4. After upload, check dashboard
1. Refresh http://localhost:3000/dashboard
2. New contract should appear in list

---

## Quick Test Checklist

### Backend (curl)

| Test | Command | Expected |
|------|---------|----------|
| ✅ Health | `curl http://localhost:8000/health` | `{"status":"ok"}` |
| ✅ Protected (no token) | `curl http://localhost:8000/api/v1/contracts/` | `401` |
| ✅ Protected (with JWT) | `curl ... -H "Authorization: Bearer JWT"` | `200` + data |
| ✅ Upload | `POST /api/v1/upload/` with JWT | `201` + job_id |
| ✅ Webhook | Sign up on frontend | User created in DB |

### Frontend (Browser)

| Test | Action | Expected |
|------|--------|----------|
| ✅ Sign Up | Create account | User in database |
| ✅ Sign In | Login | Redirect to dashboard |
| ✅ Dashboard | View page | Shows contracts |
| ✅ Upload | Upload file | Creates Contract + ScanJob |
| ✅ Sidebar | View sidebar | Shows recent contracts |

---

## Troubleshooting

### "Token has expired"
- Get fresh JWT from browser: DevTools → Application → Local Storage → `__session`

### "401 Unauthorized"
- JWT may be invalid or expired
- Sign out and sign in again to get new token

### Upload returns 422
- Check that all required fields are sent:
  - `file_url`
  - `original_filename`
  - `file_type`
  - `file_size_bytes`

### Frontend shows "No contracts"
- Upload a file first
- Or check browser console for errors
- Verify API call succeeds in Network tab

---

## Testing New Features After Phase 3

When testing new features (Phase 4+):

1. **Get JWT**: Sign in to frontend, copy from Local Storage
2. **Test with curl**: Verify backend works
3. **Test with frontend**: Verify UI works
4. **Check database**: Verify records created

---

*Last updated: May 2026*