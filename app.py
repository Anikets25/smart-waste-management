"""
app.py  —  Smart Waste Management System
─────────────────────────────────────────
Three separate portals, all backed by the same MySQL database:

  / (landing)                    — portal selector (Citizen / Admin / Staff)
  /citizen/*                     — citizen registration, login, dashboard, complaints, rewards
  /admin/*                       — admin login, dashboard, complaint mgmt, staff mgmt, rewards
  /staff/*                       — staff login, task list, status updates, after-photo upload

All existing public routes (/report, /track, /about) are preserved.
"""

import os
import functools
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, abort,
)
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from utils.helpers import (
    get_db_connection,
    generate_complaint_id,
    generate_employee_id,
    save_uploaded_file,
    format_datetime,
    award_green_points,
    GREEN_POINTS_PER_COMPLAINT,
    STATUS_INFO,
)


# ─────────────────────────────────────────────────────────────────────────────
#  App factory
# ─────────────────────────────────────────────────────────────────────────────

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Jinja2 helpers ────────────────────────────────────────────────────
    @app.template_filter("format_dt")
    def format_dt_filter(dt):
        return format_datetime(dt)

    @app.context_processor
    def inject_globals():
        return dict(STATUS_INFO=STATUS_INFO)


    # ═════════════════════════════════════════════════════════════════════════
    #  AUTH DECORATORS  —  one per portal, completely independent
    # ═════════════════════════════════════════════════════════════════════════

    def citizen_required(fn):
        @functools.wraps(fn)
        def wrap(*a, **kw):
            if not session.get("citizen_id"):
                flash("Please log in to access your dashboard.", "warning")
                return redirect(url_for("citizen_login", next=request.path))
            return fn(*a, **kw)
        return wrap

    def admin_required(fn):
        @functools.wraps(fn)
        def wrap(*a, **kw):
            if not session.get("admin_logged_in"):
                flash("Admin login required.", "warning")
                return redirect(url_for("admin_login", next=request.path))
            return fn(*a, **kw)
        return wrap

    def staff_required(fn):
        @functools.wraps(fn)
        def wrap(*a, **kw):
            if not session.get("staff_id"):
                flash("Please log in to access the staff portal.", "warning")
                return redirect(url_for("staff_login", next=request.path))
            return fn(*a, **kw)
        return wrap


    # ═════════════════════════════════════════════════════════════════════════
    #  LANDING PAGE
    # ═════════════════════════════════════════════════════════════════════════

    @app.route("/")
    def landing():
        """Portal selector — citizen / admin / staff."""
        return render_template("landing.html")


    # ═════════════════════════════════════════════════════════════════════════
    #  CITIZEN PORTAL
    # ═════════════════════════════════════════════════════════════════════════

    @app.route("/citizen/register", methods=["GET", "POST"])
    def citizen_register():
        if session.get("citizen_id"):
            return redirect(url_for("citizen_dashboard"))

        if request.method == "GET":
            return render_template("citizen/register.html", form={})

        name     = request.form.get("name",     "").strip()
        email    = request.form.get("email",    "").strip().lower()
        phone    = request.form.get("phone",    "").strip() or None
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm",  "")

        errors = []
        if not name:              errors.append("Name is required.")
        if not email or "@" not in email: errors.append("A valid email is required.")
        if len(password) < 8:    errors.append("Password must be at least 8 characters.")
        if password != confirm:  errors.append("Passwords do not match.")

        if errors:
            for e in errors: flash(e, "error")
            return render_template("citizen/register.html",
                                   form={"name": name, "email": email, "phone": phone}), 400

        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM citizens WHERE email = %s LIMIT 1", (email,))
            if cursor.fetchone():
                flash("An account with that email already exists. Please log in.", "error")
                cursor.close(); conn.close()
                return render_template("citizen/register.html",
                                       form={"name": name, "email": email, "phone": phone}), 400

            cursor.execute(
                "INSERT INTO citizens (name, email, phone, password_hash) VALUES (%s,%s,%s,%s)",
                (name, email, phone, generate_password_hash(password)),
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Registration failed: {e}", "error")
            return render_template("citizen/register.html",
                                   form={"name": name, "email": email, "phone": phone}), 500

        session.clear()
        session["citizen_id"]    = new_id
        session["citizen_name"]  = name
        session["citizen_email"] = email
        flash(f"Welcome, {name}! Your account has been created.", "success")
        return redirect(url_for("citizen_dashboard"))


    @app.route("/citizen/login", methods=["GET", "POST"])
    def citizen_login():
        if session.get("citizen_id"):
            return redirect(url_for("citizen_dashboard"))

        error = None
        if request.method == "POST":
            email    = request.form.get("email",    "").strip().lower()
            password = request.form.get("password", "")

            try:
                conn   = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM citizens WHERE email = %s AND is_active = 1 LIMIT 1",
                    (email,),
                )
                citizen = cursor.fetchone()
                cursor.close(); conn.close()
            except Exception:
                error = "Database error. Please try again."
                citizen = None

            if citizen and check_password_hash(citizen["password_hash"], password):
                session.clear()
                session["citizen_id"]    = citizen["id"]
                session["citizen_name"]  = citizen["name"]
                session["citizen_email"] = citizen["email"]
                next_url = request.args.get("next")
                if next_url and next_url.startswith("/citizen"):
                    return redirect(next_url)
                return redirect(url_for("citizen_dashboard"))
            else:
                error = "Invalid email or password."

        return render_template("citizen/login.html", error=error)


    @app.route("/citizen/logout")
    def citizen_logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("citizen_login"))


    @app.route("/citizen/dashboard")
    @citizen_required
    def citizen_dashboard():
        citizen_id = session["citizen_id"]
        stats      = {}
        recent     = []
        citizen    = {}

        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM citizens WHERE id = %s", (citizen_id,))
            citizen = cursor.fetchone() or {}

            cursor.execute(
                "SELECT COUNT(*) AS n FROM complaints WHERE citizen_id = %s",
                (citizen_id,)
            )
            stats["total"] = cursor.fetchone()["n"]

            for s, k in [("Submitted","submitted"),("Under Review","under_review"),
                         ("In Progress","in_progress"),("Resolved","resolved")]:
                cursor.execute(
                    "SELECT COUNT(*) AS n FROM complaints WHERE citizen_id=%s AND status=%s",
                    (citizen_id, s)
                )
                stats[k] = cursor.fetchone()["n"]

            cursor.execute(
                "SELECT * FROM complaints WHERE citizen_id=%s ORDER BY created_at DESC LIMIT 5",
                (citizen_id,)
            )
            recent = cursor.fetchall()
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Could not load dashboard: {e}", "error")

        return render_template("citizen/dashboard.html",
                               citizen=citizen, stats=stats, recent=recent)


    @app.route("/citizen/report", methods=["GET", "POST"])
    @citizen_required
    def citizen_report():
        if request.method == "GET":
            return render_template("citizen/report.html", form_data=None)

        description = request.form.get("description", "").strip()
        category    = request.form.get("category",    "").strip()
        location    = request.form.get("location",    "").strip()
        image_file  = request.files.get("image")
        citizen_id  = session["citizen_id"]

        errors = []
        if len(description) < 10: errors.append("Description must be at least 10 characters.")
        if category not in {"Plastic","Wet Waste","Dry Waste","Other"}:
            errors.append("Please select a valid category.")
        if not location: errors.append("Location is required.")

        if errors:
            for e in errors: flash(e, "error")
            return render_template("citizen/report.html",
                form_data={"description":description,"category":category,"location":location}), 400

        image_path = None
        if image_file and image_file.filename:
            image_path = save_uploaded_file(image_file)
            if image_path is None:
                flash("Invalid image. PNG/JPG/GIF/WEBP, max 5 MB.", "error")
                return render_template("citizen/report.html",
                    form_data={"description":description,"category":category,"location":location}), 400

        complaint_id = generate_complaint_id()
        try:
            conn   = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO complaints
                   (complaint_id, citizen_id, description, category, location, image_path, status)
                   VALUES (%s,%s,%s,%s,%s,%s,'Submitted')""",
                (complaint_id, citizen_id, description, category, location, image_path),
            )
            conn.commit()
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Could not save complaint: {e}", "error")
            return render_template("citizen/report.html",
                form_data={"description":description,"category":category,"location":location}), 500

        flash(f"Complaint submitted! Your ID is {complaint_id}", "success")
        return redirect(url_for("citizen_my_complaints"))


    @app.route("/citizen/complaints")
    @citizen_required
    def citizen_my_complaints():
        citizen_id = session["citizen_id"]
        complaints = []
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM complaints WHERE citizen_id=%s ORDER BY created_at DESC",
                (citizen_id,)
            )
            complaints = cursor.fetchall()
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Error loading complaints: {e}", "error")
        return render_template("citizen/complaints.html", complaints=complaints)


    @app.route("/citizen/complaint/<complaint_id_str>")
    @citizen_required
    def citizen_complaint_detail(complaint_id_str):
        citizen_id = session["citizen_id"]
        complaint  = None
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            # Row-level security: citizen can only see their own complaints
            cursor.execute(
                "SELECT * FROM complaints WHERE complaint_id=%s AND citizen_id=%s LIMIT 1",
                (complaint_id_str.upper(), citizen_id),
            )
            complaint = cursor.fetchone()
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Error: {e}", "error")
        if not complaint:
            abort(404)
        return render_template("citizen/complaint_detail.html", complaint=complaint)


    @app.route("/citizen/rewards")
    @citizen_required
    def citizen_rewards():
        citizen_id = session["citizen_id"]
        rewards    = []
        citizen    = {}
        history    = []
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT green_points FROM citizens WHERE id=%s", (citizen_id,))
            citizen = cursor.fetchone() or {"green_points": 0}
            cursor.execute("SELECT * FROM rewards WHERE is_active=1 ORDER BY points_cost")
            rewards = cursor.fetchall()
            cursor.execute(
                """SELECT rr.*, r.name AS reward_name
                   FROM reward_redemptions rr
                   JOIN rewards r ON r.id = rr.reward_id
                   WHERE rr.citizen_id=%s ORDER BY rr.created_at DESC LIMIT 10""",
                (citizen_id,)
            )
            history = cursor.fetchall()
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Error loading rewards: {e}", "error")
        return render_template("citizen/rewards.html", rewards=rewards,
                               citizen=citizen, history=history)


    @app.route("/citizen/rewards/redeem/<int:reward_id>", methods=["POST"])
    @citizen_required
    def citizen_redeem(reward_id):
        citizen_id = session["citizen_id"]
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM rewards WHERE id=%s AND is_active=1 LIMIT 1", (reward_id,))
            reward = cursor.fetchone()
            cursor.execute("SELECT green_points FROM citizens WHERE id=%s", (citizen_id,))
            citizen = cursor.fetchone()

            if not reward:
                flash("Reward not found.", "error")
            elif reward["stock"] < 1:
                flash("This reward is out of stock.", "error")
            elif citizen["green_points"] < reward["points_cost"]:
                flash(f"Not enough Green Points. You need {reward['points_cost']} but have {citizen['green_points']}.", "error")
            else:
                cursor.execute(
                    "UPDATE citizens SET green_points = green_points - %s WHERE id = %s",
                    (reward["points_cost"], citizen_id)
                )
                cursor.execute(
                    "UPDATE rewards SET stock = stock - 1 WHERE id = %s",
                    (reward_id,)
                )
                cursor.execute(
                    "INSERT INTO reward_redemptions (citizen_id, reward_id, points_spent) VALUES (%s,%s,%s)",
                    (citizen_id, reward_id, reward["points_cost"])
                )
                cursor.execute(
                    "INSERT INTO green_points_log (citizen_id, points, reason) VALUES (%s,%s,%s)",
                    (citizen_id, -reward["points_cost"], f"Redeemed: {reward['name']}")
                )
                conn.commit()
                flash(f"🎉 Successfully redeemed '{reward['name']}'! Your request is pending approval.", "success")
                cursor.close(); conn.close()
                return redirect(url_for("citizen_rewards"))

            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Redemption failed: {e}", "error")
        return redirect(url_for("citizen_rewards"))


    @app.route("/citizen/profile", methods=["GET", "POST"])
    @citizen_required
    def citizen_profile():
        citizen_id = session["citizen_id"]
        citizen    = {}
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM citizens WHERE id=%s", (citizen_id,))
            citizen = cursor.fetchone() or {}

            if request.method == "POST":
                name  = request.form.get("name",  "").strip()
                phone = request.form.get("phone", "").strip() or None
                if not name:
                    flash("Name is required.", "error")
                else:
                    cursor.execute(
                        "UPDATE citizens SET name=%s, phone=%s WHERE id=%s",
                        (name, phone, citizen_id)
                    )
                    conn.commit()
                    session["citizen_name"] = name
                    flash("Profile updated successfully.", "success")
                    citizen["name"]  = name
                    citizen["phone"] = phone

            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Error: {e}", "error")
        return render_template("citizen/profile.html", citizen=citizen)


    # ═════════════════════════════════════════════════════════════════════════
    #  ADMIN PORTAL
    # ═════════════════════════════════════════════════════════════════════════

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if session.get("admin_logged_in"):
            return redirect(url_for("admin_dashboard"))

        error = None
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            try:
                conn   = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM admins WHERE username=%s LIMIT 1", (username,))
                admin  = cursor.fetchone()
                cursor.close(); conn.close()
            except Exception:
                error = "Database error. Please try again."
                admin = None

            if admin and check_password_hash(admin["password_hash"], password):
                session.clear()
                session["admin_logged_in"] = True
                session["admin_username"]  = admin["username"]
                session["admin_id"]        = admin["id"]
                next_url = request.args.get("next")
                if next_url and next_url.startswith("/admin"):
                    return redirect(next_url)
                return redirect(url_for("admin_dashboard"))
            else:
                error = "Invalid username or password."

        return render_template("admin/login.html", error=error, username="")


    @app.route("/admin/logout")
    def admin_logout():
        session.clear()
        flash("Logged out.", "info")
        return redirect(url_for("admin_login"))


    @app.route("/admin/dashboard")
    @admin_required
    def admin_dashboard():
        stats = {}; category_stats = []; recent = []
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) AS n FROM complaints")
            stats["total"] = cursor.fetchone()["n"]
            for s, k in [("Submitted","submitted"),("Under Review","under_review"),
                         ("In Progress","in_progress"),("Resolved","resolved")]:
                cursor.execute("SELECT COUNT(*) AS n FROM complaints WHERE status=%s", (s,))
                stats[k] = cursor.fetchone()["n"]
            cursor.execute("SELECT COUNT(*) AS n FROM citizens")
            stats["citizens"] = cursor.fetchone()["n"]
            cursor.execute("SELECT COUNT(*) AS n FROM staff")
            stats["staff"] = cursor.fetchone()["n"]
            cursor.execute(
                "SELECT category, COUNT(*) AS count FROM complaints GROUP BY category ORDER BY count DESC"
            )
            category_stats = cursor.fetchall()
            cursor.execute(
                """SELECT c.*, ct.name AS citizen_name
                   FROM complaints c LEFT JOIN citizens ct ON ct.id=c.citizen_id
                   ORDER BY c.created_at DESC LIMIT 10"""
            )
            recent = cursor.fetchall()
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Dashboard error: {e}", "error")
        return render_template("admin/dashboard.html", stats=stats,
                               category_stats=category_stats, recent=recent)


    @app.route("/admin/complaints")
    @admin_required
    def admin_complaints():
        search   = request.args.get("search",   "").strip()
        status   = request.args.get("status",   "").strip()
        category = request.args.get("category", "").strip()

        query  = """SELECT c.*, ct.name AS citizen_name, s.name AS staff_name
                    FROM complaints c
                    LEFT JOIN citizens ct ON ct.id = c.citizen_id
                    LEFT JOIN staff     s  ON s.id  = c.assigned_staff_id
                    WHERE 1=1"""
        params = []
        if search:
            query  += " AND (c.complaint_id LIKE %s OR c.location LIKE %s)"
            like    = f"%{search}%"
            params += [like, like]
        if status:
            query  += " AND c.status = %s"; params.append(status)
        if category:
            query  += " AND c.category = %s"; params.append(category)
        query += " ORDER BY c.created_at DESC"

        complaints = []
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            complaints = cursor.fetchall()
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Error: {e}", "error")

        return render_template("admin/complaints.html", complaints=complaints,
                               total=len(complaints),
                               filters={"search":search,"status":status,"category":category})


    @app.route("/admin/complaint/<int:cid>")
    @admin_required
    def admin_complaint_detail(cid):
        complaint = None; staff_list = []
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT c.*, ct.name AS citizen_name, s.name AS staff_name
                   FROM complaints c
                   LEFT JOIN citizens ct ON ct.id=c.citizen_id
                   LEFT JOIN staff    s  ON s.id =c.assigned_staff_id
                   WHERE c.id=%s LIMIT 1""",
                (cid,)
            )
            complaint = cursor.fetchone()
            cursor.execute("SELECT id, name, employee_id, zone FROM staff WHERE is_active=1 ORDER BY name")
            staff_list = cursor.fetchall()
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Error: {e}", "error")
        if not complaint: abort(404)
        return render_template("admin/complaint_detail.html",
                               complaint=complaint, staff_list=staff_list)


    @app.route("/admin/complaint/<int:cid>/update-status", methods=["POST"])
    @admin_required
    def admin_update_status(cid):
        new_status = request.form.get("status", "").strip()
        if new_status not in {"Submitted","Under Review","In Progress","Resolved"}:
            flash("Invalid status.", "error")
            return redirect(url_for("admin_complaint_detail", cid=cid))
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Fetch complaint to check current state and citizen linkage
            cursor.execute(
                "SELECT id, citizen_id, status, green_points_awarded FROM complaints WHERE id=%s",
                (cid,)
            )
            comp = cursor.fetchone()
            cursor.close()

            if comp:
                cursor2 = conn.cursor()
                cursor2.execute("UPDATE complaints SET status=%s WHERE id=%s", (new_status, cid))

                # Award Green Points when resolved (only once)
                if new_status == "Resolved" and comp["citizen_id"] and comp["green_points_awarded"] == 0:
                    award_green_points(conn, comp["citizen_id"], cid,
                                       GREEN_POINTS_PER_COMPLAINT,
                                       "Complaint resolved — thank you for reporting!")
                conn.commit()
                cursor2.close()
                flash(f"Status updated to '{new_status}'.", "success")
            conn.close()
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin_complaint_detail", cid=cid))


    @app.route("/admin/complaint/<int:cid>/assign", methods=["POST"])
    @admin_required
    def admin_assign_staff(cid):
        staff_id = request.form.get("staff_id", "").strip()
        try:
            conn   = get_db_connection()
            cursor = conn.cursor()
            if staff_id:
                cursor.execute(
                    "UPDATE complaints SET assigned_staff_id=%s WHERE id=%s",
                    (int(staff_id), cid)
                )
            else:
                cursor.execute(
                    "UPDATE complaints SET assigned_staff_id=NULL WHERE id=%s", (cid,)
                )
            conn.commit(); cursor.close(); conn.close()
            flash("Staff assignment updated.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin_complaint_detail", cid=cid))


    # ── Admin: Staff management ───────────────────────────────────────────

    @app.route("/admin/staff")
    @admin_required
    def admin_staff_list():
        staff = []
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT s.*, COUNT(c.id) AS assigned_count
                   FROM staff s
                   LEFT JOIN complaints c ON c.assigned_staff_id=s.id AND c.status != 'Resolved'
                   GROUP BY s.id ORDER BY s.name"""
            )
            staff = cursor.fetchall()
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Error: {e}", "error")
        return render_template("admin/staff_list.html", staff=staff)


    @app.route("/admin/staff/add", methods=["GET", "POST"])
    @admin_required
    def admin_add_staff():
        if request.method == "GET":
            return render_template("admin/staff_add.html", form={})

        name     = request.form.get("name",     "").strip()
        email    = request.form.get("email",    "").strip().lower()
        phone    = request.form.get("phone",    "").strip() or None
        zone     = request.form.get("zone",     "").strip() or None
        password = request.form.get("password", "")

        errors = []
        if not name:   errors.append("Name is required.")
        if not email or "@" not in email: errors.append("Valid email required.")
        if len(password) < 8: errors.append("Password must be at least 8 characters.")

        if errors:
            for e in errors: flash(e, "error")
            return render_template("admin/staff_add.html",
                                   form={"name":name,"email":email,"phone":phone,"zone":zone}), 400

        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM staff WHERE email=%s LIMIT 1", (email,))
            if cursor.fetchone():
                flash("A staff member with that email already exists.", "error")
                cursor.close(); conn.close()
                return render_template("admin/staff_add.html",
                                       form={"name":name,"email":email,"phone":phone,"zone":zone}), 400

            emp_id = generate_employee_id()
            cursor.execute(
                """INSERT INTO staff (name, email, phone, password_hash, employee_id, zone, created_by_admin)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (name, email, phone, generate_password_hash(password),
                 emp_id, zone, session["admin_id"])
            )
            conn.commit(); cursor.close(); conn.close()
            flash(f"Staff member '{name}' added. Employee ID: {emp_id}", "success")
            return redirect(url_for("admin_staff_list"))
        except Exception as e:
            flash(f"Error: {e}", "error")
            return render_template("admin/staff_add.html",
                                   form={"name":name,"email":email,"phone":phone,"zone":zone}), 500


    @app.route("/admin/staff/<int:sid>/toggle", methods=["POST"])
    @admin_required
    def admin_toggle_staff(sid):
        try:
            conn   = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE staff SET is_active = 1 - is_active WHERE id=%s", (sid,)
            )
            conn.commit(); cursor.close(); conn.close()
            flash("Staff status updated.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin_staff_list"))


    # ── Admin: Rewards management ─────────────────────────────────────────

    @app.route("/admin/rewards")
    @admin_required
    def admin_rewards():
        rewards = []; redemptions = []
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM rewards ORDER BY is_active DESC, points_cost")
            rewards = cursor.fetchall()
            cursor.execute(
                """SELECT rr.*, r.name AS reward_name, ct.name AS citizen_name
                   FROM reward_redemptions rr
                   JOIN rewards r ON r.id=rr.reward_id
                   JOIN citizens ct ON ct.id=rr.citizen_id
                   WHERE rr.status='Pending' ORDER BY rr.created_at DESC"""
            )
            redemptions = cursor.fetchall()
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Error: {e}", "error")
        return render_template("admin/rewards.html", rewards=rewards, redemptions=redemptions)


    @app.route("/admin/rewards/redemption/<int:rid>/approve", methods=["POST"])
    @admin_required
    def admin_approve_redemption(rid):
        try:
            conn   = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE reward_redemptions SET status='Approved' WHERE id=%s AND status='Pending'",
                (rid,)
            )
            conn.commit(); cursor.close(); conn.close()
            flash("Redemption approved.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin_rewards"))


    @app.route("/admin/rewards/redemption/<int:rid>/reject", methods=["POST"])
    @admin_required
    def admin_reject_redemption(rid):
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            # Return points to citizen
            cursor.execute(
                "SELECT citizen_id, points_spent FROM reward_redemptions WHERE id=%s LIMIT 1",
                (rid,)
            )
            rr = cursor.fetchone()
            if rr:
                cursor2 = conn.cursor()
                cursor2.execute(
                    "UPDATE citizens SET green_points = green_points + %s WHERE id=%s",
                    (rr["points_spent"], rr["citizen_id"])
                )
                cursor2.execute(
                    "UPDATE reward_redemptions SET status='Rejected' WHERE id=%s", (rid,)
                )
                cursor2.execute(
                    "INSERT INTO green_points_log (citizen_id, points, reason) VALUES (%s,%s,%s)",
                    (rr["citizen_id"], rr["points_spent"], "Redemption rejected — points refunded")
                )
                conn.commit(); cursor2.close()
            cursor.close(); conn.close()
            flash("Redemption rejected and points refunded.", "info")
        except Exception as e:
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin_rewards"))


    # ═════════════════════════════════════════════════════════════════════════
    #  STAFF PORTAL
    # ═════════════════════════════════════════════════════════════════════════

    @app.route("/staff/login", methods=["GET", "POST"])
    def staff_login():
        if session.get("staff_id"):
            return redirect(url_for("staff_dashboard"))

        error = None
        if request.method == "POST":
            email    = request.form.get("email",    "").strip().lower()
            password = request.form.get("password", "")
            try:
                conn   = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM staff WHERE email=%s AND is_active=1 LIMIT 1", (email,)
                )
                staff  = cursor.fetchone()
                cursor.close(); conn.close()
            except Exception:
                error = "Database error."
                staff = None

            if staff and check_password_hash(staff["password_hash"], password):
                session.clear()
                session["staff_id"]   = staff["id"]
                session["staff_name"] = staff["name"]
                session["staff_emp"]  = staff["employee_id"]
                next_url = request.args.get("next")
                if next_url and next_url.startswith("/staff"):
                    return redirect(next_url)
                return redirect(url_for("staff_dashboard"))
            else:
                error = "Invalid email or password."

        return render_template("staff/login.html", error=error)


    @app.route("/staff/logout")
    def staff_logout():
        session.clear()
        flash("Logged out.", "info")
        return redirect(url_for("staff_login"))


    @app.route("/staff/dashboard")
    @staff_required
    def staff_dashboard():
        staff_id = session["staff_id"]
        tasks    = []; stats = {}
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT * FROM complaints WHERE assigned_staff_id=%s
                   ORDER BY FIELD(status,'In Progress','Under Review','Submitted','Resolved'),
                            created_at DESC""",
                (staff_id,)
            )
            tasks = cursor.fetchall()
            stats["total"]       = len(tasks)
            stats["in_progress"] = sum(1 for t in tasks if t["status"] == "In Progress")
            stats["resolved"]    = sum(1 for t in tasks if t["status"] == "Resolved")
            stats["pending"]     = sum(1 for t in tasks if t["status"] in ("Submitted","Under Review"))
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Error: {e}", "error")
        return render_template("staff/dashboard.html", tasks=tasks, stats=stats)


    @app.route("/staff/task/<int:cid>")
    @staff_required
    def staff_task_detail(cid):
        staff_id  = session["staff_id"]
        complaint = None
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            # Row-level security: staff sees only their assigned tasks
            cursor.execute(
                "SELECT * FROM complaints WHERE id=%s AND assigned_staff_id=%s LIMIT 1",
                (cid, staff_id)
            )
            complaint = cursor.fetchone()
            cursor.close(); conn.close()
        except Exception as e:
            flash(f"Error: {e}", "error")
        if not complaint: abort(404)
        return render_template("staff/task_detail.html", complaint=complaint)


    @app.route("/staff/task/<int:cid>/update", methods=["POST"])
    @staff_required
    def staff_update_task(cid):
        staff_id    = session["staff_id"]
        new_status  = request.form.get("status", "").strip()
        after_image = request.files.get("after_image")

        # Staff may only set In Progress or Resolved on their own tasks
        if new_status not in {"In Progress", "Resolved"}:
            flash("Invalid status.", "error")
            return redirect(url_for("staff_task_detail", cid=cid))

        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, citizen_id, assigned_staff_id, status, green_points_awarded FROM complaints WHERE id=%s LIMIT 1",
                (cid,)
            )
            comp = cursor.fetchone()
            if not comp or comp["assigned_staff_id"] != staff_id:
                flash("Task not found or not assigned to you.", "error")
                cursor.close(); conn.close()
                return redirect(url_for("staff_dashboard"))

            after_path = None
            if after_image and after_image.filename:
                after_path = save_uploaded_file(after_image, subfolder="after")
                if after_path is None:
                    flash("Invalid image. PNG/JPG/GIF/WEBP, max 5 MB.", "error")
                    cursor.close(); conn.close()
                    return redirect(url_for("staff_task_detail", cid=cid))

            cursor2 = conn.cursor()
            if after_path:
                cursor2.execute(
                    "UPDATE complaints SET status=%s, after_image_path=%s WHERE id=%s",
                    (new_status, after_path, cid)
                )
            else:
                cursor2.execute("UPDATE complaints SET status=%s WHERE id=%s", (new_status, cid))

            # Award points when staff marks resolved
            if new_status == "Resolved" and comp["citizen_id"] and comp["green_points_awarded"] == 0:
                award_green_points(conn, comp["citizen_id"], cid,
                                   GREEN_POINTS_PER_COMPLAINT,
                                   "Complaint resolved — thank you for reporting!")

            conn.commit(); cursor2.close(); cursor.close(); conn.close()
            flash(f"Task updated to '{new_status}'.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")

        return redirect(url_for("staff_task_detail", cid=cid))


    # ═════════════════════════════════════════════════════════════════════════
    #  PRESERVED PUBLIC ROUTES (unchanged from original)
    # ═════════════════════════════════════════════════════════════════════════

    @app.route("/report", methods=["GET", "POST"])
    def report():
        if request.method == "GET":
            return render_template("report.html", form_data=None)

        description = request.form.get("description","").strip()
        category    = request.form.get("category",   "").strip()
        location    = request.form.get("location",   "").strip()
        image_file  = request.files.get("image")

        errors = []
        if len(description) < 10: errors.append("Description must be at least 10 characters.")
        if category not in {"Plastic","Wet Waste","Dry Waste","Other"}:
            errors.append("Please select a valid waste category.")
        if not location: errors.append("Location is required.")

        if errors:
            for e in errors: flash(e, "error")
            return render_template("report.html",
                form_data={"description":description,"category":category,"location":location}), 400

        image_path = None
        if image_file and image_file.filename:
            saved = save_uploaded_file(image_file)
            if saved is None:
                flash("Invalid image. PNG/JPG/GIF/WEBP, max 5 MB.", "error")
                return render_template("report.html",
                    form_data={"description":description,"category":category,"location":location}), 400
            image_path = saved

        complaint_id = generate_complaint_id()
        try:
            conn   = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO complaints
                   (complaint_id, description, category, location, image_path, status)
                   VALUES (%s,%s,%s,%s,%s,'Submitted')""",
                (complaint_id, description, category, location, image_path),
            )
            conn.commit(); cursor.close(); conn.close()
        except Exception as e:
            flash("Could not save your complaint. Please try again.", "error")
            return render_template("report.html",
                form_data={"description":description,"category":category,"location":location}), 500

        return render_template("success.html",
            complaint_id=complaint_id,
            submitted_at=format_datetime(datetime.now()),
            category=category, location=location)


    @app.route("/track")
    def track():
        query_id  = request.args.get("id","").strip().upper()
        complaint = None; error = None
        if query_id:
            try:
                conn   = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM complaints WHERE complaint_id=%s LIMIT 1", (query_id,)
                )
                complaint = cursor.fetchone()
                cursor.close(); conn.close()
            except Exception:
                error = "Could not retrieve complaint. Please try again."
            if not complaint and not error:
                error = f'No complaint found with ID "{query_id}".'
        return render_template("track.html", complaint=complaint,
                               query_id=query_id, error=error)


    @app.route("/about")
    def about():
        return render_template("about.html")


    @app.route("/db-test")
    def db_test():
        try:
            conn   = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE()")
            db = cursor.fetchone()[0]
            cursor.close(); conn.close()
            return jsonify({"status":"success","database":db})
        except Exception as e:
            return jsonify({"status":"error","message":str(e)}), 500


    # ── Error handlers ────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        flash("File too large. Maximum size is 5 MB.", "error")
        return redirect(request.referrer or url_for("landing"))

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
