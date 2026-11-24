# Smart Waste Management System — Testing Checklist

Manual test cases to verify the application before submission.

---

## Setup Checks

- [ ] `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` completes without errors
- [ ] `mysql -u root -p < database/schema.sql` creates `smart_waste_db`, `admins`, and `complaints` tables
- [ ] `.env` created from `.env.example` with correct DB credentials
- [ ] `python create_admin.py` creates an admin successfully
- [ ] `python app.py` starts Flask on `http://127.0.0.1:5000`
- [ ] `http://127.0.0.1:5000/db-test` returns `{"status": "success"}`

---

## Public Pages

### Homepage
- [ ] Homepage loads correctly
- [ ] Navigation links are visible and functional
- [ ] Stats bar shows numbers (may be 0 on first run)
- [ ] "Report Waste Now" button navigates to `/report`
- [ ] "Track My Complaint" button navigates to `/track`
- [ ] Quick-track form submits with a complaint ID
- [ ] Site is responsive (resize to 375px width, check mobile nav)
- [ ] Mobile hamburger menu opens and closes

### Report Waste Page
- [ ] Form loads with all fields (description, category, location, photo)
- [ ] Submitting empty form shows validation errors on all required fields
- [ ] Description shorter than 10 characters triggers error
- [ ] Invalid category value is rejected (server-side tested via curl/Postman)
- [ ] Empty location triggers error
- [ ] Uploading a `.txt` file is rejected with error message
- [ ] Uploading a file over 5 MB shows error message
- [ ] Valid form without photo submits successfully
- [ ] Valid form with valid image (JPG < 5 MB) submits successfully
- [ ] Success page shows complaint ID, timestamp, category, location
- [ ] Complaint ID format: `WMS-YYYYMMDD-XXXXXX`
- [ ] "Copy ID" button copies to clipboard

### Track Complaint Page
- [ ] Empty search shows validation error
- [ ] Non-existent complaint ID shows "not found" message
- [ ] Valid complaint ID shows all complaint details
- [ ] Status timeline shows correct step highlighted
- [ ] Uploaded photo appears (if present)
- [ ] Photo can be clicked to open lightbox
- [ ] Lightbox closes on click and on Escape key

### About Page
- [ ] Page loads correctly with team names and project info

---

## Admin Module

### Login
- [ ] `/admin/dashboard` without login redirects to `/admin/login`
- [ ] `/admin/complaints` without login redirects to `/admin/login`
- [ ] Login with wrong username/password shows vague error
- [ ] Login with correct credentials redirects to dashboard
- [ ] After login, session persists on page refresh

### Dashboard
- [ ] All 5 stat cards show (Total, Submitted, Under Review, In Progress, Resolved)
- [ ] Category breakdown chart appears
- [ ] Recent complaints table shows latest 10
- [ ] "View" button on each row navigates to complaint detail

### Complaints List
- [ ] All complaints appear in the table
- [ ] Search by complaint ID filters results
- [ ] Search by location text filters results
- [ ] Filter by status filters correctly
- [ ] Filter by category filters correctly
- [ ] Combining search + status + category works
- [ ] "Clear" link resets all filters
- [ ] No results shows empty state message

### Complaint Detail
- [ ] All complaint fields are displayed
- [ ] Status timeline shows correct current step
- [ ] Uploaded photo is displayed (if present)
- [ ] Photo opens in lightbox
- [ ] "Download Image" link works
- [ ] Status dropdown contains all 4 status values
- [ ] Updating status saves and shows success flash message
- [ ] Updated status is reflected immediately in the timeline

### Logout
- [ ] "Logout" clears session
- [ ] After logout, trying to visit `/admin/dashboard` redirects to login

---

## Security Tests

- [ ] Visiting `/admin/dashboard` while logged out returns redirect, not page content
- [ ] SQL injection attempt in complaint ID field (e.g. `' OR 1=1 --`) returns "not found", not data
- [ ] File named `../../etc/passwd` is renamed safely (UUID filename)
- [ ] `.env` file is not accessible via browser (`http://localhost:5000/.env` returns 404)
- [ ] `static/uploads/` only contains image files (`.gitkeep` allowed)

---

## Responsive / UI
- [ ] All pages render correctly on 375px (mobile)
- [ ] All pages render correctly on 768px (tablet)
- [ ] All pages render correctly on 1200px (desktop)
- [ ] Flash messages auto-dismiss after 5 seconds
- [ ] Flash messages can be manually closed

---

## Edge Cases
- [ ] Submitting complaint with Unicode characters in description works
- [ ] Submitting complaint with very long location (254 chars) works
- [ ] Two concurrent submissions get different complaint IDs
- [ ] Uploading a valid image with a capital extension (.JPG) is accepted
