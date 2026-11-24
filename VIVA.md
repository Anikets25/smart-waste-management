# Smart Waste Management System — Viva Questions & Answers

Prepared for B.Tech final year project evaluation.

---

## General / Project Overview

**Q: What problem does your project solve?**  
A: Citizens often have no structured way to report local waste problems — they post on social media or rely on word of mouth, with no tracking or accountability. Our system provides a web platform to submit formal complaints, receive a unique tracking ID, and follow the complaint lifecycle from submission to resolution, while giving administrators a centralised management interface.

**Q: What is the main workflow of the system?**  
A: A citizen visits the site, fills in the Report Waste form with a description, category, location, and optional photo, and receives a unique complaint ID (e.g. WMS-20241115-A3F9K2). An administrator logs into the protected admin area, reviews all complaints, and updates their status. The citizen can enter their complaint ID on the Track page at any time to see the current status and details.

**Q: Why did you choose a web application over a mobile app?**  
A: A web application is accessible on any device with a browser — mobile or desktop — without requiring installation. It was also within the scope of our B.Tech project timeline and technology stack.

---

## Technology Stack

**Q: Why Flask instead of Django?**  
A: Flask is a micro-framework that gives us full control over structure without imposing unnecessary conventions. For a project of this scale (a few pages and routes), Django's ORM, admin panel, and app system would be over-engineering. Flask keeps the code readable for a small team.

**Q: Why MySQL instead of MongoDB?**  
A: Our data is highly structured — complaints have fixed, well-defined fields and clear relationships. A relational database with an ENUM for status and proper constraints is the right tool. MySQL enforces data integrity at the database level, which MongoDB does not by default.

**Q: Why Vanilla JavaScript instead of React?**  
A: The frontend logic is simple — form validation, a file preview, a nav toggle, and auto-dismiss messages. Adding React would introduce a build step, state management, and dependency complexity for no measurable gain. Vanilla JS is easier for the team to understand and maintain.

---

## Database

**Q: Explain your database schema.**  
A: We have two tables. `admins` stores admin credentials — id, username, and a password_hash (never plain text). `complaints` stores each report with: a unique complaint_id string (e.g. WMS-20241115-A3F9K2), description, category, location, an optional image_path, a status ENUM, and created_at/updated_at timestamps.

**Q: Why use an ENUM for status instead of a VARCHAR?**  
A: ENUM restricts the column to only the defined values (`Submitted`, `Under Review`, `In Progress`, `Resolved`). This enforces data integrity at the database level — invalid status values cannot be inserted, even if there were a bug in application-layer validation.

**Q: What indexes does your complaints table have?**  
A: Three: `idx_complaints_status` for status-based filtering (used by the admin dashboard and filter), `idx_complaints_category` for category filtering, and `idx_complaints_created` for chronological ordering. The `complaint_id` column also has a unique index for fast lookups on the Track page.

**Q: How is the unique complaint ID generated?**  
A: In Python using `generate_complaint_id()` in `utils/helpers.py`. The format is `WMS-YYYYMMDD-XXXXXX` where the date portion comes from `datetime.now()` and the 6-character suffix is chosen randomly from uppercase letters and digits (A–Z, 0–9). That gives 36^6 ≈ 2.17 billion possible combinations per day, which is far more than sufficient.

---

## Security

**Q: How are admin passwords stored?**  
A: Using Werkzeug's `generate_password_hash()`, which applies PBKDF2-HMAC-SHA256 with a random salt. The plain-text password is never stored. When an admin logs in, `check_password_hash()` verifies the input against the stored hash without ever decoding it.

**Q: How do you prevent SQL injection?**  
A: All database queries use parameterized statements with the `%s` placeholder through `mysql-connector-python`. Values are always passed as a separate tuple, never concatenated into the query string. For example: `cursor.execute("SELECT * FROM complaints WHERE complaint_id = %s", (query_id,))`.

**Q: How do you prevent unsafe file uploads?**  
A: Three layers: (1) Extension whitelist — only PNG, JPG, GIF, WEBP are accepted. (2) `secure_filename()` from Werkzeug strips dangerous characters and path separators. (3) The filename is replaced with a UUID, so the user's original filename never reaches the filesystem.

**Q: How do you protect admin routes?**  
A: The `@admin_required` decorator checks `session["admin_logged_in"]` before each admin view function. If the session flag is not set, the user is redirected to the login page. This is applied to every admin route except login itself.

**Q: How do you prevent session fixation attacks?**  
A: We call `session.clear()` immediately before writing any data into the session on successful login. This ensures the authenticated session always has a fresh session ID, not one that was present before login.

**Q: What is XSS and how is it prevented here?**  
A: Cross-Site Scripting (XSS) is when malicious JavaScript is injected into a page and executed in another user's browser. Jinja2 auto-escapes all variables rendered in templates by default (`{{ variable }}` escapes HTML entities), so user-submitted text cannot inject script tags.

**Q: What is the SECRET_KEY used for?**  
A: Flask uses it to cryptographically sign the session cookie. Without a correct SECRET_KEY, an attacker cannot forge a valid session cookie. It is loaded from `.env` and never hard-coded in source.

---

## Application Logic

**Q: What happens when a user submits the Report Waste form?**  
A: (1) Client-side JS validates the form before submission. (2) Flask's route receives the POST request and re-validates all fields server-side. (3) If an image was uploaded, it is validated and saved with a UUID filename. (4) A unique complaint ID is generated. (5) The complaint is inserted into MySQL with status 'Submitted'. (6) The success page is rendered showing the complaint ID.

**Q: What happens if the MySQL insert fails after the image is already saved?**  
A: The exception handler deletes the saved image file before returning the error response. This prevents orphaned files from accumulating in the uploads folder.

**Q: Can a complaint ID ever collide?**  
A: Theoretically yes — with 36^6 ≈ 2 billion combinations per day. For an academic project running locally, the probability is negligible. In production, a `UNIQUE` constraint on the `complaint_id` column ensures the database rejects duplicates, and we could add a retry loop in `generate_complaint_id()`.

**Q: How does the admin filter work?**  
A: The admin complaints route reads `search`, `status`, and `category` from query parameters and builds a SQL query dynamically by appending `WHERE` clauses. All values are passed as parameterized arguments — there is no string formatting of user input into the query.

---

## Design

**Q: Why is the design green-themed?**  
A: Green is universally associated with sustainability and environmental awareness, which is appropriate for a waste management application. The consistent colour palette (defined as CSS custom properties / variables) also makes the design system easy to extend and modify.

**Q: How is the application responsive?**  
A: Through CSS flexbox, CSS Grid, and three breakpoints in `style.css` (768px and 480px). The navigation collapses to a hamburger menu on mobile. Cards and form layouts switch from multi-column to single-column. Font sizes are reduced on small screens.

---

## Future Work

**Q: What would you add given more time?**  
A: (1) Email notifications to citizens when status changes. (2) Pagination on the admin complaint list. (3) Admin notes/comments on individual complaints. (4) A heatmap showing complaint hotspots by neighbourhood. (5) AI-based image classification to auto-suggest the waste category. (6) Data export (CSV or PDF report) from the admin panel.

**Q: How would you deploy this for real use?**  
A: Use a production WSGI server like Gunicorn, serve static files and proxy requests through Nginx, deploy on a VPS or cloud VM (AWS EC2, DigitalOcean Droplet), use a managed MySQL service or run MySQL on the same server, enable HTTPS via Let's Encrypt, set `SESSION_COOKIE_SECURE=True` in `.env`, and move `static/uploads` to object storage (S3, Cloudflare R2) for scalability.
