from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os
from datetime import date, datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "himi_secret_2026"
DB = os.path.join(os.path.dirname(__file__), "himi.db")

# ── DB helpers ────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db(); c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        class_group TEXT,
        subject TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        author TEXT NOT NULL,
        tag TEXT DEFAULT 'General',
        created_by INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        teacher TEXT NOT NULL,
        score INTEGER NOT NULL,
        grade TEXT NOT NULL,
        term TEXT DEFAULT 'Term 2',
        FOREIGN KEY(student_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        subject TEXT NOT NULL,
        teacher TEXT NOT NULL,
        due_date TEXT NOT NULL,
        type TEXT DEFAULT 'assignment',
        status TEXT DEFAULT 'pending',
        assigned_to INTEGER,
        created_by INTEGER,
        file_name TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        student_name TEXT NOT NULL,
        day TEXT NOT NULL,
        period TEXT NOT NULL,
        status TEXT NOT NULL,
        week TEXT DEFAULT '2026-W12',
        FOREIGN KEY(student_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        description TEXT,
        content TEXT,
        teacher TEXT NOT NULL,
        class_group TEXT,
        created_by INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT NOT NULL,
        period TEXT NOT NULL,
        subject TEXT NOT NULL,
        teacher TEXT NOT NULL,
        room TEXT,
        class_group TEXT NOT NULL
    );
    """)

    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        # Students: lysa, amel, thanina
        # Teachers: Mr. LALLAL AHMAD, Ms. SI HADJ MOHAND KENZA, Mme. LAZIB KATIA
        # Admin: id=7
        users = [
            ("lysa",     generate_password_hash("student123"), "Lysa",                    "student", "M1A", None),
            ("amel",     generate_password_hash("student123"), "Amel",                    "student", "M1A", None),
            ("thanina",  generate_password_hash("student123"), "Thanina",                 "student", "M1B", None),
            ("lallal",   generate_password_hash("teacher123"), "Mr. LALLAL AHMAD",        "teacher", None, "Introduction to Networks"),
            ("sihadj",   generate_password_hash("teacher123"), "Ms. SI HADJ MOHAND KENZA","teacher", None, "Linux Server"),
            ("lazib",    generate_password_hash("teacher123"), "Mme. LAZIB KATIA",        "teacher", None, "Windows Server"),
            ("admin",    generate_password_hash("admin123"),   "Administration",           "admin",   None, None),
        ]
        c.executemany("INSERT INTO users(username,password,full_name,role,class_group,subject) VALUES(?,?,?,?,?,?)", users)

        anns = [
            ("Exam Schedule — June 2026", "The final examination schedule for June 2026 has been published. Students are advised to consult the timetable section for their individual schedules.", "Administration", "Academic"),
            ("Registration Deadline", "The registration deadline for the new academic year 2026–2027 is set for 30 April 2026. Please ensure all documents are submitted to the secretariat.", "Administration", "Administrative"),
            ("IT Infrastructure Workshop — 20 April", "HIMI will host an IT Infrastructure Workshop on 20 April 2026. All students in the Networks and Cloud track are encouraged to attend.", "Administration", "Events"),
        ]
        c.executemany("INSERT INTO announcements(title,body,author,tag,created_by) VALUES(?,?,?,?,7)", anns)

        # Grades for Lysa (id=1), Amel (id=2), Thanina (id=3)
        # Mr. LALLAL: Introduction to Networks, Cloud Infrastructure, Multi-Platform Project
        # Ms. SI HADJ MOHAND: Linux Server, Python, Algorithm
        # Mme. LAZIB: Windows Server, VoIP
        grades_data = [
            (1,"Introduction to Networks","Mr. LALLAL AHMAD",87,"A"),
            (1,"Cloud Infrastructure","Mr. LALLAL AHMAD",82,"A"),
            (1,"Multi-Platform Project","Mr. LALLAL AHMAD",90,"A+"),
            (1,"Linux Server","Ms. SI HADJ MOHAND KENZA",75,"B+"),
            (1,"Python","Ms. SI HADJ MOHAND KENZA",88,"A"),
            (1,"Algorithm","Ms. SI HADJ MOHAND KENZA",79,"B+"),
            (1,"Windows Server","Mme. LAZIB KATIA",84,"A"),
            (1,"VoIP","Mme. LAZIB KATIA",77,"B+"),
            (2,"Introduction to Networks","Mr. LALLAL AHMAD",80,"B+"),
            (2,"Cloud Infrastructure","Mr. LALLAL AHMAD",74,"B"),
            (2,"Linux Server","Ms. SI HADJ MOHAND KENZA",85,"A"),
            (2,"Python","Ms. SI HADJ MOHAND KENZA",91,"A+"),
            (2,"Windows Server","Mme. LAZIB KATIA",78,"B+"),
            (2,"VoIP","Mme. LAZIB KATIA",72,"B"),
            (3,"Introduction to Networks","Mr. LALLAL AHMAD",83,"A"),
            (3,"Multi-Platform Project","Mr. LALLAL AHMAD",88,"A"),
            (3,"Algorithm","Ms. SI HADJ MOHAND KENZA",76,"B+"),
            (3,"Windows Server","Mme. LAZIB KATIA",81,"A"),
        ]
        c.executemany("INSERT INTO grades(student_id,subject,teacher,score,grade) VALUES(?,?,?,?,?)", grades_data)

        # Lessons: teacher ids are 4=lallal, 5=sihadj, 6=lazib
        lessons_data = [
            ("OSI Model and Network Layers",
             "Introduction to Networks",
             "Understanding the 7-layer OSI model and how data travels across a network.",
             "Layer 1 (Physical) to Layer 7 (Application) — roles, protocols, and data encapsulation at each layer. Comparison with the TCP/IP model. Practical examples using Wireshark to capture and analyse packets.",
             "Mr. LALLAL AHMAD","M1A",4),

            ("Cloud Computing Fundamentals",
             "Cloud Infrastructure",
             "Introduction to cloud service models: IaaS, PaaS, and SaaS, and major cloud providers.",
             "Definitions of IaaS, PaaS, SaaS with real-world examples (AWS EC2, Google App Engine, Office 365). Public vs private vs hybrid cloud. Key concepts: elasticity, scalability, pay-as-you-go pricing.",
             "Mr. LALLAL AHMAD","M1A",4),

            ("Cross-Platform Development Concepts",
             "Multi-Platform Project",
             "Planning and structuring a software project that runs on multiple operating systems and environments.",
             "Choosing a cross-platform framework (Electron, Flutter, React Native). Version control with Git. Project structure best practices. Setting up a shared development environment.",
             "Mr. LALLAL AHMAD","M1B",4),

            ("Linux File System and Permissions",
             "Linux Server",
             "Navigating the Linux file system hierarchy and managing file permissions and ownership.",
             "Filesystem Hierarchy Standard (FHS): /etc, /var, /home, /usr. chmod, chown, chgrp commands with examples. Special permissions: setuid, setgid, sticky bit. Practical: creating users and managing access on Ubuntu Server.",
             "Ms. SI HADJ MOHAND KENZA","M1A",5),

            ("Python Functions and Modules",
             "Python",
             "Writing reusable code with Python functions and organising projects with modules and packages.",
             "Defining functions with def, parameters, return values, and default arguments. *args and **kwargs. Importing standard library modules (os, sys, math). Creating and importing custom modules. Practical: building a simple file management script.",
             "Ms. SI HADJ MOHAND KENZA","M1A",5),

            ("Introduction to Algorithms and Complexity",
             "Algorithm",
             "Fundamental algorithmic thinking, sorting algorithms, and Big-O complexity analysis.",
             "What is an algorithm? Flowcharts and pseudocode. Sorting: Bubble Sort, Selection Sort, Merge Sort — step-by-step with complexity analysis. Big-O notation: O(1), O(n), O(n²), O(log n). Practical: implementing and comparing sort algorithms in Python.",
             "Ms. SI HADJ MOHAND KENZA","M1B",5),

            ("Windows Server Installation and Roles",
             "Windows Server",
             "Installing Windows Server and configuring core server roles including Active Directory and DNS.",
             "Windows Server editions overview. Step-by-step installation in a virtual machine. Configuring Active Directory Domain Services (AD DS). Setting up DNS and DHCP server roles. Practical: joining a workstation to the domain.",
             "Mme. LAZIB KATIA","M1A",6),

            ("VoIP Protocols and Architecture",
             "VoIP",
             "Understanding Voice over IP technology, SIP protocol, and practical VoIP system setup.",
             "What is VoIP and how it differs from traditional telephony. SIP (Session Initiation Protocol) — call setup and teardown. RTP (Real-time Transport Protocol) for media streaming. Codecs: G.711, G.729. Practical: configuring a basic SIP softphone using Zoiper.",
             "Mme. LAZIB KATIA","M1B",6),
        ]
        c.executemany("INSERT INTO lessons(title,subject,description,content,teacher,class_group,created_by) VALUES(?,?,?,?,?,?,?)", lessons_data)

        # Assignments: assigned_to 1=lysa, 2=amel, 3=thanina
        assignments_data = [
            ("Network Topology Lab Report",
             "Design and document a small office network topology using Packet Tracer. Include IP addressing plan, router and switch configuration.",
             "Introduction to Networks","Mr. LALLAL AHMAD","2026-03-28","assignment","pending",1,4),

            ("Cloud Provider Comparison",
             "Write a 1000-word report comparing AWS, Azure, and Google Cloud. Focus on pricing, storage services, and compute options.",
             "Cloud Infrastructure","Mr. LALLAL AHMAD","2026-03-25","assignment","overdue",2,4),

            ("Cross-Platform App Prototype",
             "Create a simple cross-platform to-do application using Flutter or Electron. Submit source code and a short demonstration video.",
             "Multi-Platform Project","Mr. LALLAL AHMAD","2026-04-05","assignment","pending",3,4),

            ("Linux User Management Script",
             "Write a Bash script that automates the creation of 5 users with specific permissions and home directories on a Linux server.",
             "Linux Server","Ms. SI HADJ MOHAND KENZA","2026-03-22","assignment","overdue",1,5),

            ("Python File Organiser",
             "Develop a Python script that sorts files in a directory by extension into subfolders. Handle exceptions and add logging.",
             "Python","Ms. SI HADJ MOHAND KENZA","2026-04-02","assignment","pending",2,5),

            ("Algorithm Complexity Analysis",
             "Implement Bubble Sort and Merge Sort in Python. Measure execution time for arrays of 100, 1000, and 10000 elements and plot the results.",
             "Algorithm","Ms. SI HADJ MOHAND KENZA","2026-03-30","assignment","pending",3,5),

            ("Active Directory Setup Report",
             "Set up a Windows Server domain in a virtual environment. Document each step with screenshots and explain the role of each service configured.",
             "Windows Server","Mme. LAZIB KATIA","2026-04-08","assignment","pending",1,6),

            ("VoIP System Configuration",
             "Configure a SIP-based VoIP communication between two softphones on the same local network. Document the setup and test call quality.",
             "VoIP","Mme. LAZIB KATIA","2026-03-26","assignment","pending",2,6),
        ]
        c.executemany("INSERT INTO assignments(title,description,subject,teacher,due_date,type,status,assigned_to,created_by) VALUES(?,?,?,?,?,?,?,?,?)", assignments_data)

        tt_data = [
            ("Monday","08:00-10:00","Introduction to Networks","Mr. LALLAL AHMAD","Room A101","M1A"),
            ("Monday","10:15-12:15","Linux Server","Ms. SI HADJ MOHAND KENZA","Lab L1","M1A"),
            ("Monday","13:30-15:30","Windows Server","Mme. LAZIB KATIA","Lab L2","M1A"),
            ("Tuesday","08:00-10:00","Cloud Infrastructure","Mr. LALLAL AHMAD","Room A101","M1A"),
            ("Tuesday","10:15-12:15","Python","Ms. SI HADJ MOHAND KENZA","Lab L1","M1A"),
            ("Tuesday","13:30-15:30","VoIP","Mme. LAZIB KATIA","Lab L2","M1A"),
            ("Wednesday","08:00-10:00","Multi-Platform Project","Mr. LALLAL AHMAD","Room A102","M1B"),
            ("Wednesday","10:15-12:15","Algorithm","Ms. SI HADJ MOHAND KENZA","Lab L1","M1B"),
            ("Wednesday","13:30-15:30","Windows Server","Mme. LAZIB KATIA","Lab L2","M1B"),
            ("Thursday","08:00-10:00","Introduction to Networks","Mr. LALLAL AHMAD","Room A101","M1B"),
            ("Thursday","10:15-12:15","Linux Server","Ms. SI HADJ MOHAND KENZA","Lab L1","M1B"),
            ("Thursday","13:30-15:30","VoIP","Mme. LAZIB KATIA","Lab L2","M1B"),
            ("Friday","08:00-10:00","Cloud Infrastructure","Mr. LALLAL AHMAD","Room A101","M1A"),
            ("Friday","10:15-12:15","Algorithm","Ms. SI HADJ MOHAND KENZA","Lab L1","M1A"),
            ("Friday","13:30-15:30","Multi-Platform Project","Mr. LALLAL AHMAD","Room A102","M1B"),
        ]
        c.executemany("INSERT INTO timetable(day,period,subject,teacher,room,class_group) VALUES(?,?,?,?,?,?)", tt_data)

        att_data = [
            (1,"Lysa","Monday","08:00-10:00","Present","2026-W12"),
            (1,"Lysa","Monday","10:15-12:15","Present","2026-W12"),
            (1,"Lysa","Tuesday","08:00-10:00","Absent","2026-W12"),
            (1,"Lysa","Tuesday","10:15-12:15","Present","2026-W12"),
            (1,"Lysa","Wednesday","08:00-10:00","Late","2026-W12"),
            (2,"Amel","Monday","08:00-10:00","Present","2026-W12"),
            (2,"Amel","Monday","10:15-12:15","Present","2026-W12"),
            (2,"Amel","Tuesday","08:00-10:00","Present","2026-W12"),
            (2,"Amel","Tuesday","10:15-12:15","Late","2026-W12"),
            (3,"Thanina","Monday","08:00-10:00","Present","2026-W12"),
            (3,"Thanina","Tuesday","10:15-12:15","Absent","2026-W12"),
            (3,"Thanina","Wednesday","08:00-10:00","Present","2026-W12"),
        ]
        c.executemany("INSERT INTO attendance(student_id,student_name,day,period,status,week) VALUES(?,?,?,?,?,?)", att_data)

    conn.commit(); conn.close()

# ── Auth ──────────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("role") not in roles:
                flash("Access denied.", "error")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated
    return decorator

def current_user():
    if "user_id" not in session: return None
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close(); return u

app.jinja_env.globals.update(enumerate=enumerate, current_user=current_user)

# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])
def login():
    if "user_id" in session: return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"]   = user["id"]
            session["role"]      = user["role"]
            session["full_name"] = user["full_name"]
            session["username"]  = user["username"]
            return redirect(url_for("dashboard"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db(); role = session["role"]; uid = session["user_id"]
    ann = conn.execute("SELECT * FROM announcements ORDER BY id DESC LIMIT 4").fetchall()
    if role == "student":
        grades = conn.execute("SELECT * FROM grades WHERE student_id=?", (uid,)).fetchall()
        avg    = round(sum(g["score"] for g in grades)/len(grades)) if grades else 0
        pending = conn.execute("SELECT COUNT(*) as n FROM assignments WHERE assigned_to=? AND status!='done'", (uid,)).fetchone()["n"]
        stats  = {"avg": avg, "pending": pending}
    elif role == "teacher":
        subj   = conn.execute("SELECT subject FROM users WHERE id=?", (uid,)).fetchone()["subject"]
        students = conn.execute("SELECT COUNT(*) as n FROM users WHERE role='student'").fetchone()["n"]
        tasks  = conn.execute("SELECT COUNT(*) as n FROM assignments WHERE teacher=?", (subj,)).fetchone()["n"]
        lessons = conn.execute("SELECT COUNT(*) as n FROM lessons WHERE created_by=?", (uid,)).fetchone()["n"]
        stats  = {"subject": subj, "students": students, "tasks": tasks, "lessons": lessons}
    else:
        stats  = {
            "students": conn.execute("SELECT COUNT(*) as n FROM users WHERE role='student'").fetchone()["n"],
            "teachers": conn.execute("SELECT COUNT(*) as n FROM users WHERE role='teacher'").fetchone()["n"],
            "announcements": conn.execute("SELECT COUNT(*) as n FROM announcements").fetchone()["n"],
            "lessons": conn.execute("SELECT COUNT(*) as n FROM lessons").fetchone()["n"],
        }
    conn.close()
    return render_template("dashboard.html", page="dashboard", ann=ann, stats=stats)

# ── Announcements ─────────────────────────────────────────────────────────────
@app.route("/announcements")
@login_required
def announcements():
    conn = get_db()
    anns = conn.execute("SELECT * FROM announcements ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("announcements.html", page="announcements", announcements=anns)

@app.route("/announcements/add", methods=["GET","POST"])
@login_required
@role_required("admin","teacher")
def add_announcement():
    if request.method == "POST":
        conn = get_db()
        conn.execute("INSERT INTO announcements(title,body,author,tag,created_by) VALUES(?,?,?,?,?)",
            (request.form["title"], request.form["body"], session["full_name"], request.form["tag"], session["user_id"]))
        conn.commit(); conn.close()
        flash("Announcement published.", "success")
        return redirect(url_for("announcements"))
    return render_template("add_announcement.html", page="announcements")

@app.route("/announcements/delete/<int:aid>")
@login_required
@role_required("admin")
def delete_announcement(aid):
    conn = get_db(); conn.execute("DELETE FROM announcements WHERE id=?", (aid,)); conn.commit(); conn.close()
    flash("Announcement deleted.", "success"); return redirect(url_for("announcements"))

# ── Grades ────────────────────────────────────────────────────────────────────
@app.route("/grades")
@login_required
def grades():
    conn = get_db(); uid = session["user_id"]; role = session["role"]
    if role == "student":
        gs   = conn.execute("SELECT * FROM grades WHERE student_id=?", (uid,)).fetchall()
        avg  = round(sum(g["score"] for g in gs)/len(gs)) if gs else 0
        best = max(gs, key=lambda g: g["score"]) if gs else None
        conn.close()
        return render_template("grades.html", page="grades", grades=gs, avg=avg, best=best)
    else:
        students_list = conn.execute("SELECT * FROM users WHERE role='student' ORDER BY full_name").fetchall()
        all_grades    = conn.execute("""
            SELECT g.*, u.full_name as student_name, u.class_group
            FROM grades g JOIN users u ON g.student_id=u.id ORDER BY u.full_name, g.subject
        """).fetchall()
        conn.close()
        return render_template("grades_all.html", page="grades", grades=all_grades, students=students_list)

@app.route("/grades/add", methods=["GET","POST"])
@login_required
@role_required("admin","teacher")
def add_grade():
    conn = get_db()
    if request.method == "POST":
        conn.execute("INSERT INTO grades(student_id,subject,teacher,score,grade) VALUES(?,?,?,?,?)",
            (request.form["student_id"], request.form["subject"], session["full_name"],
             int(request.form["score"]), request.form["grade"]))
        conn.commit(); conn.close()
        flash("Grade recorded.", "success"); return redirect(url_for("grades"))
    students = conn.execute("SELECT * FROM users WHERE role='student' ORDER BY full_name").fetchall()
    conn.close()
    return render_template("add_grade.html", page="grades", students=students)

@app.route("/grades/delete/<int:gid>")
@login_required
@role_required("admin")
def delete_grade(gid):
    conn = get_db(); conn.execute("DELETE FROM grades WHERE id=?", (gid,)); conn.commit(); conn.close()
    flash("Grade deleted.", "success"); return redirect(url_for("grades"))

# ── Attendance ────────────────────────────────────────────────────────────────
@app.route("/attendance")
@login_required
def attendance():
    conn = get_db(); uid = session["user_id"]; role = session["role"]
    days  = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
    slots = ["08:00-10:00","10:15-12:15","13:30-15:30"]
    if role == "student":
        rows = conn.execute("SELECT * FROM attendance WHERE student_id=? AND week='2026-W12'", (uid,)).fetchall()
        att  = {d: {} for d in days}
        for r in rows: att[r["day"]][r["period"]] = r["status"]
        total   = len(rows)
        present = sum(1 for r in rows if r["status"]=="Present")
        absent  = sum(1 for r in rows if r["status"]=="Absent")
        late    = sum(1 for r in rows if r["status"]=="Late")
        rate    = round(present/total*100) if total else 0
        conn.close()
        return render_template("attendance.html", page="attendance",
            att=att, days=days, slots=slots, rate=rate, present=present, absent=absent, late=late)
    else:
        students = conn.execute("SELECT * FROM users WHERE role='student' ORDER BY full_name").fetchall()
        summary  = conn.execute("""
            SELECT u.id, u.full_name, u.class_group,
                COUNT(*) as total,
                SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN a.status='Absent'  THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN a.status='Late'    THEN 1 ELSE 0 END) as late
            FROM attendance a JOIN users u ON a.student_id=u.id GROUP BY u.id
        """).fetchall()
        conn.close()
        return render_template("attendance_all.html", page="attendance",
            summary=summary, students=students, days=days, slots=slots)

@app.route("/attendance/add", methods=["GET","POST"])
@login_required
@role_required("admin","teacher")
def add_attendance():
    conn = get_db()
    if request.method == "POST":
        sid  = request.form["student_id"]
        sname = conn.execute("SELECT full_name FROM users WHERE id=?", (sid,)).fetchone()["full_name"]
        conn.execute("INSERT OR REPLACE INTO attendance(student_id,student_name,day,period,status,week) VALUES(?,?,?,?,?,?)",
            (sid, sname, request.form["day"], request.form["period"], request.form["status"], "2026-W12"))
        conn.commit(); conn.close()
        flash("Attendance recorded.", "success"); return redirect(url_for("attendance"))
    students = conn.execute("SELECT * FROM users WHERE role='student' ORDER BY full_name").fetchall()
    conn.close()
    return render_template("add_attendance.html", page="attendance", students=students)

# ── Assignments ───────────────────────────────────────────────────────────────
@app.route("/assignments")
@login_required
def assignments():
    conn = get_db(); uid = session["user_id"]; role = session["role"]
    if role == "student":
        pending = conn.execute("SELECT * FROM assignments WHERE assigned_to=? AND status='pending' ORDER BY due_date", (uid,)).fetchall()
        overdue = conn.execute("SELECT * FROM assignments WHERE assigned_to=? AND status='overdue' ORDER BY due_date", (uid,)).fetchall()
        done    = conn.execute("SELECT * FROM assignments WHERE assigned_to=? AND status='done' ORDER BY due_date DESC", (uid,)).fetchall()
        conn.close()
        return render_template("assignments.html", page="assignments", pending=pending, overdue=overdue, done=done)
    else:
        all_a = conn.execute("""
            SELECT a.*, u.full_name as student_name FROM assignments a
            LEFT JOIN users u ON a.assigned_to=u.id ORDER BY a.due_date
        """).fetchall()
        conn.close()
        return render_template("assignments_all.html", page="assignments", assignments=all_a)

@app.route("/assignments/add", methods=["GET","POST"])
@login_required
@role_required("admin","teacher")
def add_assignment():
    conn = get_db()
    if request.method == "POST":
        sid = request.form.get("student_id") or None
        conn.execute("INSERT INTO assignments(title,description,subject,teacher,due_date,assigned_to,created_by) VALUES(?,?,?,?,?,?,?)",
            (request.form["title"], request.form.get("description",""),
             request.form["subject"], session["full_name"],
             request.form["due_date"], sid, session["user_id"]))
        conn.commit(); conn.close()
        flash("Assignment published.", "success"); return redirect(url_for("assignments"))
    students = conn.execute("SELECT * FROM users WHERE role='student' ORDER BY full_name").fetchall()
    subjects = [r["subject"] for r in conn.execute("SELECT DISTINCT subject FROM grades").fetchall()]
    if not subjects: subjects = ["Management","Finance","Marketing","Business Law","Statistics"]
    conn.close()
    return render_template("add_assignment.html", page="assignments", students=students, subjects=subjects)

@app.route("/assignments/complete/<int:aid>")
@login_required
def complete_assignment(aid):
    conn = get_db(); conn.execute("UPDATE assignments SET status='done' WHERE id=?", (aid,)); conn.commit(); conn.close()
    flash("Marked as completed.", "success"); return redirect(url_for("assignments"))

@app.route("/assignments/delete/<int:aid>")
@login_required
@role_required("admin","teacher")
def delete_assignment(aid):
    conn = get_db(); conn.execute("DELETE FROM assignments WHERE id=?", (aid,)); conn.commit(); conn.close()
    flash("Assignment deleted.", "success"); return redirect(url_for("assignments"))

# ── Lessons ───────────────────────────────────────────────────────────────────
@app.route("/lessons")
@login_required
def lessons():
    conn = get_db(); uid = session["user_id"]; role = session["role"]
    if role == "student":
        cg = conn.execute("SELECT class_group FROM users WHERE id=?", (uid,)).fetchone()["class_group"]
        ls = conn.execute("SELECT * FROM lessons WHERE class_group=? OR class_group IS NULL ORDER BY id DESC", (cg,)).fetchall()
    elif role == "teacher":
        ls = conn.execute("SELECT * FROM lessons WHERE created_by=? ORDER BY id DESC", (uid,)).fetchall()
    else:
        ls = conn.execute("SELECT * FROM lessons ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("lessons.html", page="lessons", lessons=ls)

@app.route("/lessons/add", methods=["GET","POST"])
@login_required
@role_required("admin","teacher")
def add_lesson():
    conn = get_db()
    if request.method == "POST":
        classes = request.form.get("class_group") or None
        conn.execute("INSERT INTO lessons(title,subject,description,content,teacher,class_group,created_by) VALUES(?,?,?,?,?,?,?)",
            (request.form["title"], request.form["subject"], request.form.get("description",""),
             request.form.get("content",""), session["full_name"], classes, session["user_id"]))
        conn.commit(); conn.close()
        flash("Lesson published.", "success"); return redirect(url_for("lessons"))
    conn.close()
    return render_template("add_lesson.html", page="lessons")

@app.route("/lessons/<int:lid>")
@login_required
def view_lesson(lid):
    conn = get_db()
    lesson = conn.execute("SELECT * FROM lessons WHERE id=?", (lid,)).fetchone()
    conn.close()
    if not lesson: flash("Lesson not found.", "error"); return redirect(url_for("lessons"))
    return render_template("view_lesson.html", page="lessons", lesson=lesson)

@app.route("/lessons/delete/<int:lid>")
@login_required
@role_required("admin","teacher")
def delete_lesson(lid):
    conn = get_db(); conn.execute("DELETE FROM lessons WHERE id=?", (lid,)); conn.commit(); conn.close()
    flash("Lesson deleted.", "success"); return redirect(url_for("lessons"))

# ── Timetable ─────────────────────────────────────────────────────────────────
@app.route("/timetable")
@login_required
def timetable():
    conn = get_db(); uid = session["user_id"]; role = session["role"]
    days    = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
    periods = ["08:00-10:00","10:15-12:15","13:30-15:30"]
    if role == "student":
        cg   = conn.execute("SELECT class_group FROM users WHERE id=?", (uid,)).fetchone()["class_group"]
        rows = conn.execute("SELECT * FROM timetable WHERE class_group=?", (cg,)).fetchall()
        title = f"Timetable — Class {cg}"
    elif role == "teacher":
        name = session["full_name"]
        rows = conn.execute("SELECT * FROM timetable WHERE teacher=?", (name,)).fetchall()
        title = f"Timetable — {name}"
    else:
        rows  = conn.execute("SELECT * FROM timetable ORDER BY class_group,day").fetchall()
        title = "Full Timetable"
    # Build grid: {day: {period: row}}
    grid = {d: {p: None for p in periods} for d in days}
    for r in rows:
        if r["day"] in grid and r["period"] in grid[r["day"]]:
            grid[r["day"]][r["period"]] = r
    classes = conn.execute("SELECT DISTINCT class_group FROM timetable ORDER BY class_group").fetchall()
    teachers = conn.execute("SELECT * FROM users WHERE role='teacher' ORDER BY full_name").fetchall()
    conn.close()
    return render_template("timetable.html", page="timetable",
        grid=grid, days=days, periods=periods, title=title,
        classes=classes, teachers=teachers, role=role)

@app.route("/timetable/add", methods=["GET","POST"])
@login_required
@role_required("admin")
def add_timetable():
    conn = get_db()
    if request.method == "POST":
        conn.execute("INSERT INTO timetable(day,period,subject,teacher,room,class_group) VALUES(?,?,?,?,?,?)",
            (request.form["day"], request.form["period"], request.form["subject"],
             request.form["teacher"], request.form.get("room",""), request.form["class_group"]))
        conn.commit(); conn.close()
        flash("Timetable entry added.", "success"); return redirect(url_for("timetable"))
    teachers = conn.execute("SELECT * FROM users WHERE role='teacher' ORDER BY full_name").fetchall()
    conn.close()
    return render_template("add_timetable.html", page="timetable", teachers=teachers)

@app.route("/timetable/delete/<int:tid>")
@login_required
@role_required("admin")
def delete_timetable(tid):
    conn = get_db(); conn.execute("DELETE FROM timetable WHERE id=?", (tid,)); conn.commit(); conn.close()
    flash("Entry removed.", "success"); return redirect(url_for("timetable"))

# ── Users (admin only) ────────────────────────────────────────────────────────
@app.route("/users")
@login_required
@role_required("admin")
def users():
    conn = get_db()
    all_users = conn.execute("SELECT id,username,full_name,role,class_group,subject,created_at FROM users ORDER BY role,full_name").fetchall()
    conn.close()
    return render_template("users.html", page="users", users=all_users)

@app.route("/users/add", methods=["GET","POST"])
@login_required
@role_required("admin")
def add_user():
    if request.method == "POST":
        conn = get_db()
        try:
            conn.execute("INSERT INTO users(username,password,full_name,role,class_group,subject) VALUES(?,?,?,?,?,?)",
                (request.form["username"].lower(), generate_password_hash(request.form["password"]),
                 request.form["full_name"], request.form["role"],
                 request.form.get("class_group") or None, request.form.get("subject") or None))
            conn.commit(); flash(f"User {request.form['full_name']} created.", "success")
        except: flash("Username already exists.", "error")
        finally: conn.close()
        return redirect(url_for("users"))
    return render_template("add_user.html", page="users")

@app.route("/users/delete/<int:uid>")
@login_required
@role_required("admin")
def delete_user(uid):
    conn = get_db(); conn.execute("DELETE FROM users WHERE id=?", (uid,)); conn.commit(); conn.close()
    flash("User deleted.", "success"); return redirect(url_for("users"))

if __name__ == "__main__":
    init_db()
    print("="*55)
    print("  HIMI — Higher International Management Institute")
    print("  http://127.0.0.1:5001")
    print()
    print("  Accounts:")
    print("  Student : lysa     / student123")
    print("  Student : amel     / student123")
    print("  Student : thanina  / student123")
    print("  Teacher : lallal   / teacher123")
    print("  Teacher : sihadj   / teacher123")
    print("  Teacher : lazib    / teacher123")
    print("  Admin   : admin    / admin123")
    print("="*55)
    app.run(debug=True, port=5001)
