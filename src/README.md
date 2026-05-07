# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities (teacher-only)
- Unregister students from activities (teacher-only)
- Teacher login/logout with credentials stored in JSON

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity (teacher login required)                    |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister from an activity (teacher login required)            |
| POST   | `/auth/login`                                                     | Teacher login; returns admin token                                 |
| POST   | `/auth/logout`                                                    | Teacher logout (uses `X-Admin-Token`)                              |
| GET    | `/auth/me`                                                        | Validate current teacher session (`X-Admin-Token`)                 |

## Teacher Credentials

Teacher usernames and passwords are stored in `teachers.json` and loaded by the backend at startup.

The frontend provides a user icon in the top-right corner for teacher login. After login, signup and unregister actions are authorized with the session token.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
