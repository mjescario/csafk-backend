Citizen Science App for Kids Backend Documentation

Attached below are the current endpoints and how to utilize them in the frontend.

**Database Status**

<blockquote>

_Retrieves the current status of the connection to the DB hosted on Google Cloud._

Endpoint:

`GET /api/status`

JSON Request Requirements:

* None

CURL Example:

```
curl http://localhost:8000/api/status
```

Success Response (200)

```
{
  "status": "success",
  "message": "Connected to database successfully!"
}
```

Failure Response (500)

```
{
  "Connection Error:": "(error details")
}
```
</blockquote>

**Create Project**

<blockquote>
  
_Creates a new project, including title, description, instructions. Does not include fields (handled in a separate endpoint)._

Endpoint:

`POST /api/projects`

JSON Request Requirements:

* teacher_id
* project_title
* project_description
* project_instructions

CURL Example:

```
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "teacher_id": 1,
    "project_title": "Bumblebee Tracker",
    "project_description": "Track different bumblees you see.",
    "project_instructions": "Use the form below to fill out the type, number, and what time you saw the bumblebee."
  }
```

Success Response (201)

```
{
  "success": true,
  "message": "Project created successfully!",
  "data": {
    "project_id": 1,
    "project_code": "A82KP0QM",
    "project_title": "Bumblebee Tracker",
    "project_description": "Track different bumblees you see.",
    "project_instructions": "Use the form below to fill out the type, number, and what time you saw the bumblebee."
  }
}
```

Failure Response (400 - Client Error)

```
{
  "success": false,
  "error": "No data provided."
}
```

Failure Response (500 - Server Error)

```
{
  "Server Error:": "(error details")
}
```

</blockquote>

**Retrieve Project by ID**

<blockquote>

_Retrieves a single project's details by its ID._

Endpoint:

`GET /api/projects/{project_id}`

JSON Request Requirements:

* project_id

CURL Example:

```
curl http://localhost:8000/api/projects/1
```

Success Response (200):


```
{
  "success": true,
  "data": {
    "project_id": 1,
    "teacher_id": 1,
    "project_code": "A82KP0QM",
    "project_title": "Bumblebee Tracker",
    "project_description": "Track different bumblees you see.",
    "project_instructions": "Use the form below to fill out the type, number, and what time you saw the bumblebee."
  }
}
```

Failure Response (404 - Not Found):

```
{
  "success": false,
  "error": "Project not found.",
  "message": "No project with ID #1 exists."
}
```

Failure Response (500 - Server Error):

```
{
  "Server Error:": "(error details")
}
```

</blockquote>

**Retrieve List of Projects by Teacher**

<blockquote>

_Returns a list of projects by teacher._

Endpoint:

'GET /api/users/{teacher_id}/projects'

JSON Request Requirements:

* teacher_id

CURL Example:

```
curl http://localhost:8000/api/users/1/projects
```

Success Response (200):

```
{
  "success": true,
  "data": [
    {
      "project_id": 1,
      "teacher_id": 1,
      "project_code": "A82KP0QM",
      "project_title": "Bumblebee Tracker",
      "project_description": "Track different bumblees you see.",
      "project_instructions": "Use the form below to fill out the type, number, and what time you saw the bumblebee."
    },
    {
      "project_id": 2,
      "teacher_id": 1,
      "project_code": "TP224Z1AY",
      "project_title": "Snow Day",
      "project_description": "Track how much snow you get over the weekend.",
      "project_instructions": "Log what time and how much snow is currently outside."
    }
  ]
}
```

Failure Response (500 - Server Error):

```
{
  "Server Error:": "(error details")
}
```

</blockquote>

**Delete Project by ID**

<blockquote>

_Deletes a project (and associated data like observations) by its ID._

Endpoint:

'DELETE /api/projects/{project_id}'

JSON Request Requirements:

* project_id

CURL Example:

```
curl -X DELETE http://localhost:8000/api/projects/1
```

Success Response (200):

```
{
  "success": true,
  "message": "Project ID:1 deleted successfully."
}
```

Failure Response (404 - Not Found):

```
{
  "success": false,
  "error": "Project not found",
  "message": "No project with ID 10 exists."
}
```

Failure Response (500 - Server Error):

```
{
  "Server Error:": "(error details")
}
```

</blockquote>

**Endpoint Title**

<blockquote>

_Description_

Endpoint:

''

JSON Request Requirements:

CURL Example:

Success Response:

Failure Response:

</blockquote>
