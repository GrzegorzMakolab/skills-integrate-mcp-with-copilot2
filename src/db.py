from __future__ import annotations

import sqlite3
from pathlib import Path


class Database:
    def __init__(self, db_path: Path, schema_path: Path, seed_path: Path):
        self.db_path = db_path
        self.schema_path = schema_path
        self.seed_path = seed_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self, with_seed: bool = True) -> None:
        schema_sql = self.schema_path.read_text(encoding="utf-8")

        with self._connect() as conn:
            conn.executescript(schema_sql)
            if with_seed and self._is_empty(conn):
                seed_sql = self.seed_path.read_text(encoding="utf-8")
                conn.executescript(seed_sql)

    def reset(self) -> None:
        if self.db_path.exists():
            self.db_path.unlink()
        self.initialize(with_seed=True)

    def _is_empty(self, conn: sqlite3.Connection) -> bool:
        row = conn.execute("SELECT COUNT(1) AS total FROM activities").fetchone()
        return row is None or row["total"] == 0

    def list_activities(self) -> dict[str, dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, description, schedule, max_participants
                FROM activities
                ORDER BY name
                """
            ).fetchall()

            registrations = conn.execute(
                """
                SELECT a.name, ar.student_email
                FROM activity_registrations ar
                JOIN activities a ON a.id = ar.activity_id
                ORDER BY ar.joined_at
                """
            ).fetchall()

        participants_by_activity: dict[str, list[str]] = {}
        for reg in registrations:
            participants_by_activity.setdefault(reg["name"], []).append(reg["student_email"])

        data: dict[str, dict] = {}
        for row in rows:
            data[row["name"]] = {
                "description": row["description"],
                "schedule": row["schedule"],
                "max_participants": row["max_participants"],
                "participants": participants_by_activity.get(row["name"], []),
            }

        return data

    def _find_activity_id(self, conn: sqlite3.Connection, activity_name: str) -> int | None:
        row = conn.execute(
            "SELECT id FROM activities WHERE name = ?",
            (activity_name,),
        ).fetchone()
        if row is None:
            return None
        return int(row["id"])

    def _ensure_student(self, conn: sqlite3.Connection, email: str) -> None:
        existing = conn.execute(
            "SELECT email FROM students WHERE email = ?",
            (email,),
        ).fetchone()
        if existing:
            return

        guessed_name = email.split("@")[0].replace(".", " ").title() or email
        conn.execute(
            "INSERT INTO students (email, name, grade) VALUES (?, ?, ?)",
            (email, guessed_name, None),
        )

    def signup_for_activity(self, activity_name: str, email: str) -> None:
        with self._connect() as conn:
            activity_id = self._find_activity_id(conn, activity_name)
            if activity_id is None:
                raise ValueError("activity_not_found")

            self._ensure_student(conn, email)

            already = conn.execute(
                """
                SELECT 1 FROM activity_registrations
                WHERE activity_id = ? AND student_email = ?
                """,
                (activity_id, email),
            ).fetchone()
            if already:
                raise ValueError("already_registered")

            limits = conn.execute(
                "SELECT max_participants FROM activities WHERE id = ?",
                (activity_id,),
            ).fetchone()
            current = conn.execute(
                "SELECT COUNT(1) AS total FROM activity_registrations WHERE activity_id = ?",
                (activity_id,),
            ).fetchone()
            if limits and current and current["total"] >= limits["max_participants"]:
                raise ValueError("activity_full")

            conn.execute(
                "INSERT INTO activity_registrations (activity_id, student_email) VALUES (?, ?)",
                (activity_id, email),
            )

    def unregister_from_activity(self, activity_name: str, email: str) -> None:
        with self._connect() as conn:
            activity_id = self._find_activity_id(conn, activity_name)
            if activity_id is None:
                raise ValueError("activity_not_found")

            exists = conn.execute(
                """
                SELECT 1 FROM activity_registrations
                WHERE activity_id = ? AND student_email = ?
                """,
                (activity_id, email),
            ).fetchone()
            if not exists:
                raise ValueError("not_registered")

            conn.execute(
                "DELETE FROM activity_registrations WHERE activity_id = ? AND student_email = ?",
                (activity_id, email),
            )

    def get_student_memberships(self, student_email: str) -> list[dict]:
        with self._connect() as conn:
            student = conn.execute(
                "SELECT email, name, grade FROM students WHERE email = ?",
                (student_email,),
            ).fetchone()
            if student is None:
                raise ValueError("student_not_found")

            rows = conn.execute(
                """
                SELECT c.name AS club, c.description, scm.joined_at
                FROM student_club_memberships scm
                JOIN clubs c ON c.id = scm.club_id
                WHERE scm.student_email = ?
                ORDER BY scm.joined_at
                """,
                (student_email,),
            ).fetchall()

        return [
            {
                "club": row["club"],
                "description": row["description"],
                "joined_at": row["joined_at"],
            }
            for row in rows
        ]

    def get_advisor_memberships(self, advisor_username: str) -> list[dict]:
        with self._connect() as conn:
            advisor = conn.execute(
                "SELECT username, full_name FROM advisors WHERE username = ?",
                (advisor_username,),
            ).fetchone()
            if advisor is None:
                raise ValueError("advisor_not_found")

            rows = conn.execute(
                """
                SELECT c.name AS club, acm.position, acm.joined_at
                FROM advisor_club_memberships acm
                JOIN clubs c ON c.id = acm.club_id
                WHERE acm.advisor_username = ?
                ORDER BY acm.joined_at
                """,
                (advisor_username,),
            ).fetchall()

        return [
            {
                "club": row["club"],
                "position": row["position"],
                "joined_at": row["joined_at"],
            }
            for row in rows
        ]
