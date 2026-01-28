Citizen Science App for Kids Backend Documentation

Attached below are the current endpoints and how to utilize them in the frontend.

**Database Status**

_Retrieves the current status of the connection to the DB hosted on Google Cloud._

Endpoint:

`GET /api/status`

JSON Request:

`N/A`

Example Usage:

`curl http://localhost:8000/api/status`

Success Response (200)

`{
  "status": "success",
  "message": "Connected to database successfully!"
}`

Failure Response (500)

`{
  "Connection Error:": "(error details")
}`

**Create Project**

_Creates a new project, including title, description, instructions. Does not include fields (handled in a separate endpoint)._

Endpoint:

`POST /api/projects`

JSON Request:

{
  "teacher_id": 1,
  "project_title": "Bumblebee Tracker",
  "project_description": "Track different bumblees you see.",
  "project_instructions": "Use the form below to fill out the type, number, and what time you saw the bumblebee."
}

Example Usage:

