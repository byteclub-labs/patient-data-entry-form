#!/usr/bin/env python3
"""Patient Data Entry — single-page patient intake form.

Serves the page and its static assets, a small JSON API under /api/, and
owns the SQLite store. Python 3 standard library only.

Run: python3 server.py  ->  http://localhost:8000
"""

import json
import os
import re
import sqlite3
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = BASE_DIR / "data" / "patients.db"

MAX_BODY_BYTES = 64 * 1024
MAX_FIELD_LEN = 120
MAX_EMAIL_LEN = 254
MAX_PHONE_LEN = 40
MAX_ADDRESS_LEN = 240
MAX_POSTAL_LEN = 20
MAX_NOTES_LEN = 500
MIN_PHONE_DIGITS = 7
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PHONE_RE = re.compile(r"^\+?[0-9 ().\-]+$")

GENDERS = ("Female", "Male", "Other", "Prefer not to say")

# Exact-match path -> (file, mime) whitelist; any other path is a 404.
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/static/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/static/app.js": ("app.js", "application/javascript; charset=utf-8"),
}
API_PATHS = {"/api/patients"}
KNOWN_PATHS = set(STATIC_FILES) | API_PATHS

SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  date_of_birth TEXT NOT NULL,
  gender TEXT NOT NULL,
  phone TEXT NOT NULL,
  email TEXT NOT NULL DEFAULT '',
  street_address TEXT NOT NULL DEFAULT '',
  city TEXT NOT NULL DEFAULT '',
  state_region TEXT NOT NULL DEFAULT '',
  postal_code TEXT NOT NULL DEFAULT '',
  emergency_contact_name TEXT NOT NULL DEFAULT '',
  emergency_contact_phone TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);
"""

NOW = "strftime('%Y-%m-%dT%H:%M:%SZ','now')"

FIELDS = (
    "id", "first_name", "last_name", "date_of_birth", "gender", "phone",
    "email", "street_address", "city", "state_region", "postal_code",
    "emergency_contact_name", "emergency_contact_phone", "notes",
    "created_at",
)
SELECT_SQL = "SELECT " + ", ".join(FIELDS) + " FROM patients"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)


def _trim(value, limit):
    """Return value as a trimmed string capped at limit, '' for non-strings."""
    if not isinstance(value, str):
        return ""
    return value.strip()[:limit]


def _is_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _digit_count(value):
    return sum(1 for c in value if c.isdigit())


def _record(row):
    return dict(zip(FIELDS, row))


def handle_create_patient(body):
    """POST /api/patients — insert a new patient intake record."""
    first_name = _trim(body.get("first_name"), MAX_FIELD_LEN + 1)
    last_name = _trim(body.get("last_name"), MAX_FIELD_LEN + 1)
    date_of_birth = _trim(body.get("date_of_birth"), 11)
    gender = _trim(body.get("gender"), MAX_FIELD_LEN + 1)
    phone = _trim(body.get("phone"), MAX_PHONE_LEN + 1)
    email_raw = body.get("email")
    email = email_raw.strip().lower() if isinstance(email_raw, str) else ""
    street_address = _trim(body.get("street_address"), MAX_ADDRESS_LEN + 1)
    city = _trim(body.get("city"), MAX_FIELD_LEN + 1)
    state_region = _trim(body.get("state_region"), MAX_FIELD_LEN + 1)
    postal_code = _trim(body.get("postal_code"), MAX_POSTAL_LEN + 1)
    emergency_contact_name = _trim(
        body.get("emergency_contact_name"), MAX_FIELD_LEN + 1)
    emergency_contact_phone = _trim(
        body.get("emergency_contact_phone"), MAX_PHONE_LEN + 1)
    notes = _trim(body.get("notes"), MAX_NOTES_LEN + 1)

    if not first_name:
        return 400, {"error": "First name is required."}
    if len(first_name) > MAX_FIELD_LEN:
        return 400, {"error": "First name must be 120 characters or fewer."}
    if not last_name:
        return 400, {"error": "Last name is required."}
    if len(last_name) > MAX_FIELD_LEN:
        return 400, {"error": "Last name must be 120 characters or fewer."}
    if not DATE_RE.match(date_of_birth) or not _is_date(date_of_birth):
        return 400, {"error": "A valid date of birth is required."}
    if date_of_birth > date.today().isoformat():
        return 400, {"error": "Date of birth cannot be in the future."}
    if gender not in GENDERS:
        return 400, {"error": "Please choose a gender from the list."}
    if not phone:
        return 400, {"error": "Phone number is required."}
    if len(phone) > MAX_PHONE_LEN:
        return 400, {"error": "Phone number must be 40 characters or fewer."}
    if not PHONE_RE.match(phone) or _digit_count(phone) < MIN_PHONE_DIGITS:
        return 400, {"error": "A valid phone number is required."}
    if len(email) > MAX_EMAIL_LEN or (email and not EMAIL_RE.match(email)):
        return 400, {"error": "A valid email address is required."}
    if len(street_address) > MAX_ADDRESS_LEN:
        return 400, {"error": "Street address must be 240 characters or fewer."}
    if len(city) > MAX_FIELD_LEN:
        return 400, {"error": "City must be 120 characters or fewer."}
    if len(state_region) > MAX_FIELD_LEN:
        return 400, {"error": "State/region must be 120 characters or fewer."}
    if len(postal_code) > MAX_POSTAL_LEN:
        return 400, {"error": "ZIP/postal code must be 20 characters or fewer."}
    if len(emergency_contact_name) > MAX_FIELD_LEN:
        return 400, {
            "error": "Emergency contact name must be 120 characters or fewer."}
    if len(emergency_contact_phone) > MAX_PHONE_LEN:
        return 400, {
            "error": "Emergency contact phone must be 40 characters or fewer."}
    if (emergency_contact_phone
            and (not PHONE_RE.match(emergency_contact_phone)
                 or _digit_count(emergency_contact_phone) < MIN_PHONE_DIGITS)):
        return 400, {"error": "A valid emergency contact phone is required."}
    if len(notes) > MAX_NOTES_LEN:
        return 400, {"error": "Notes must be 500 characters or fewer."}

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO patients (first_name, last_name, date_of_birth,"
            " gender, phone, email, street_address, city, state_region,"
            " postal_code, emergency_contact_name, emergency_contact_phone,"
            f" notes, created_at)"
            f" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, {NOW})",
            (first_name, last_name, date_of_birth, gender, phone, email,
             street_address, city, state_region, postal_code,
             emergency_contact_name, emergency_contact_phone, notes),
        )
        row = conn.execute(
            SELECT_SQL + " WHERE id = ?", (cur.lastrowid,)
        ).fetchone()

    return 201, _record(row)


def list_patients():
    """GET /api/patients — every entered patient, newest first."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            SELECT_SQL + " ORDER BY created_at DESC, id DESC"
        ).fetchall()
    patients = [_record(row) for row in rows]
    return 200, patients


class PatientIntakeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    # --- helpers ---------------------------------------------------------

    def _security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'")

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filename, mime):
        path = STATIC_DIR / filename
        try:
            body = path.read_bytes()
        except OSError:
            self._send_json(404, {"error": "not found"})
            return
        self.send_response(200)
        self._security_headers()
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_body(self):
        """Parse the request body as a JSON object; returns (dict, error)."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length > MAX_BODY_BYTES:
            return None, (400, {"error": "Request body too large."})
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None, (400, {"error": "Request body must be valid JSON."})
        if not isinstance(body, dict):
            return None, (400, {"error": "Request body must be a JSON object."})
        return body, None

    def _reject(self):
        """Wrong method on a known path -> 405; anything else -> 404."""
        if self.path in KNOWN_PATHS:
            allowed = "GET" if self.path in STATIC_FILES else "GET, POST"
            self.send_response(405)
            self._security_headers()
            self.send_header("Allow", allowed)
            body = json.dumps({"error": "method not allowed"}).encode("utf-8")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self._send_json(404, {"error": "not found"})

    # --- routes ----------------------------------------------------------

    def do_GET(self):
        if self.path in STATIC_FILES:
            filename, mime = STATIC_FILES[self.path]
            self._send_file(filename, mime)
        elif self.path == "/api/patients":
            status, payload = list_patients()
            self._send_json(status, payload)
        elif self.path in KNOWN_PATHS:
            self._reject()
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/patients":
            body, error = self._json_body()
            status, payload = error or handle_create_patient(body)
            self._send_json(status, payload)
        elif self.path in KNOWN_PATHS:
            self._reject()
        else:
            self._send_json(404, {"error": "not found"})

    do_PUT = _reject
    do_PATCH = _reject
    do_DELETE = _reject
    do_HEAD = _reject


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), PatientIntakeHandler)
    print(f"Patient Data Entry running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
