Citizen Science App for Kids Backend Documentation

Attached below are the current endpoints and how to utilize them in the frontend.

Primary URL: https://csafk-277534145495.us-east4.run.app

**Database Status**

<blockquote>

_Retrieves the current status of the connection to the DB hosted on Google Cloud._

Endpoint:

`GET /api/status`

JSON Request Requirements:

* None

CURL Example:

```
curl https://csafk-277534145495.us-east4.run.app/api/status
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
curl -X POST https://csafk-277534145495.us-east4.run.app/api/projects \
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
curl https://csafk-277534145495.us-east4.run.app/api/projects/1
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
curl https://csafk-277534145495.us-east4.run.app/api/users/1/projects
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

`DELETE /api/projects/{project_id}`

JSON Request Requirements:

* project_id

CURL Example:

```
curl -X DELETE https://csafk-277534145495.us-east4.run.app/api/projects/1
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

**Add Field to Project**

<blockquote>

_Add a field (data collection point) to a project._

Endpoint:

'POST /api/projects/{project_id}/fields'

JSON Request Requirements:

* field_name (required)
* field_type (required - types: text, textarea, number, date, time, checkbox, dropdown, radio)
* field_label - label that is displayed on the page.
* field_options - JSON string for multiple choice (checkbox, dropdown, radio) options
* is_required - Boolean value (default is false) that determines if a field is required.

CURL Example:

```
curl -X POST https://csafk-277534145495.us-east4.run.app/api/projects/23/fields \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "field_name": "bird_species",
    "field_label": "Bird Species",
    "field_type": "text",
    "is_required": true
  }'
```

Success Response (201):

```
{
  "success": true,
  "message": "Field added successfully!",
  "data": {
    "field_id": 15,
    "project_id": 23,
    "field_name": "bird_species",
    "field_label": "Bird Species",
    "field_type": "text",
    "field_options": null,
    "field_required": true
  }
}
```

Failure Response (400 - Missing Fields):

```
{
  "success": false,
  "error": "field_name and field_type are required."
}
```

Failure Response (403 - Unauthorized):

```
{
  "success": false,
  "error": "Unauthorized.",
  "message": "You don't have permission to add fields to this project."
}
```

Failure Response (404 - Project Not Found):

```
{
  "success": false,
  "error": "Project not found.",
  "message": "No project with ID 99 exists."
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
