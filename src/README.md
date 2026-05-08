# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities (teacher-only)
- Unregister students from activities (teacher-only)
- Teacher login/logout with credentials stored in JSON
- Persistent relational SQLite data model for students, advisors, clubs, and memberships

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Initialize database schema and seed data:

   ```
   python init_db.py
   ```

3. Run the application:

   ```
   uvicorn app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## Database and migration/seed notes

- The app stores data in `school.db` (SQLite).
- Schema (migration baseline) lives in `db/schema.sql`.
- Seed data lives in `db/seed.sql`.
- To recreate the database from schema + seed, delete `school.db` and run:

  ```
  python init_db.py
  ```

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity (teacher login required)                    |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister from an activity (teacher login required)            |
| POST   | `/auth/login`                                                     | Teacher login; returns admin token                                 |
| POST   | `/auth/logout`                                                    | Teacher logout (uses `X-Admin-Token`)                              |
| GET    | `/auth/me`                                                        | Validate current teacher session (`X-Admin-Token`)                 |
| GET    | `/students/{student_email}/memberships`                           | Student club memberships with `joined_at`                          |
| GET    | `/advisors/{advisor_username}/memberships`                        | Advisor club memberships with `joined_at` and `position`           |

## Teacher Credentials

Teacher usernames and passwords are stored in `teachers.json` and loaded by the backend at startup.

The frontend provides a user icon in the top-right corner for teacher login. After login, signup and unregister actions are authorized with the session token.

## Data Model

The application uses a relational model with the following tables:

1. **students**
   - email (PK)
   - name
   - grade
2. **advisors**
   - username (PK)
   - full_name
3. **clubs**
   - id (PK)
   - name
   - description
4. **student_club_memberships**
   - student_email (FK)
   - club_id (FK)
   - joined_at
5. **advisor_club_memberships**
   - advisor_username (FK)
   - club_id (FK)
   - joined_at
   - position
6. **activities**
   - id (PK)
   - name
   - description
   - schedule
   - max_participants
7. **activity_registrations**
   - activity_id (FK)
   - student_email (FK)
   - joined_at

Activities endpoints are kept backward compatible while data is persisted in SQLite.
