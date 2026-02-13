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

**Get All Fields for a Project**

<blockquote>

_Retrieves all fields for a specific project._

Endpoint:

'GET /api/projects/{project_id}/fields'

JSON Request Requirements:

* project_id

CURL Example:

```
curl https://csafk-277534145495.us-east4.run.app/api/projects/23/fields \
  -H "Cookie: session=SESSION_COOKIE"
```
Note: When testing, must retrieve cookie value. Recommend using Chrome's Dev Mode to retrieve value.

Success Response (200):

```
{
  "success": true,
  "data": [
    {
      "field_id": 15,
      "project_id": 23,
      "field_name": "bird_species",
      "field_label": "Bird Species",
      "field_type": "text",
      "field_options": null,
      "field_required": true
    },
    {
      "field_id": 16,
      "project_id": 23,
      "field_name": "weather",
      "field_label": "Weather Condition",
      "field_type": "dropdown",
      "field_options": "[\"Sunny\", \"Cloudy\", \"Rainy\", \"Snowy\"]",
      "field_required": false
    }
  ]
}
```

Failure Response (403 - Unauthorized):

```
{
  "success": false,
  "error": "Unauthorized.",
  "message": "You don't have permission to view fields for this project."
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

**Update Field**

<blockquote>

_Updates an existing field in a project._

Endpoint:

'PUT /api/projects/{project_id}/fields/{field_id}'

JSON Request Requirements:

* project_id
* field_id
* fields to be updated (see types in "Add Field to a Project")

CURL Example:

```
curl -X PUT https://csafk-277534145495.us-east4.run.app/api/projects/23/fields/15 \
  -H "Content-Type: application/json" \
  -H "Cookie: session=SESSION_COOKIE" \
  -d '{
    "field_label": "Bird Species (Common Name)",
    "is_required": false
  }'
```

Success Response (200):

```
{
  "success": true,
  "message": "Field ID:15 updated successfully.",
  "data": {
    "field_id": 15,
    "project_id": 23,
    "field_label": "Bird Species (Common Name)",
    "is_required": false
  }
}
```

Failure Response (400 - Incorrect Project Field):

```
{
  "success": false,
  "error": "Field does not belong to this project."
}
```

Failure Response (403 - Unauthorized):

```
{
  "success": false,
  "error": "Unauthorized.",
  "message": "You don't have permission to update fields for this project."
}
```

Failure Response (404 - Field Not Found:

```
{
  "success": false,
  "error": "Field not found.",
  "message": "No field with ID 99 exists."
}
```

</blockquote>

**Delete Field**

<blockquote>

_Deletes a field from a project._

Endpoint:

'DELETE /api/projects/{project_id}/fields/{field_id}'

JSON Request Requirements:

* project_id
* field_id

CURL Example:

```
curl -X DELETE https://csafk-277534145495.us-east4.run.app/api/projects/23/fields/15 \
  -H "Cookie: session=SESSION_COOKIE"
```

Success Response (200):

```
{
  "success": true,
  "message": "Field ID:15 deleted successfully."
}
```

Failure Response (400 - Incorrect Project Field):

```
{
  "success": false,
  "error": "Field does not belong to this project."
}
```

Failure Response (403 - Unauthorized):

```
{
  "success": false,
  "error": "Unauthorized.",
  "message": "You don't have permission to delete fields for this project."
}
```

Failure Response (404 - Field Not Found):

```
{
  "success": false,
  "error": "Field not found.",
  "message": "No field with ID 99 exists."
}
```

</blockquote>

**Submit Observation**

<blockquote>

_Submits a new observation for a project. Does not require authentication._

Endpoint:

'POST /api/projects/{project_id}/observations'

JSON Request Requirements:

* project_id
* student_name (optional)
* field_data

CURL Example:

```
curl -X POST https://csafk-277534145495.us-east4.run.app/api/projects/23/observations \
  -H "Content-Type: application/json" \
  -d '{
    "student_name": "Alice Johnson",
    "field_data": {
      "15": "Blue Jay",
      "16": "Sunny",
      "17": "5"
    }
  }'
```

Success Response (201):

```
{
  "success": true,
  "message": "Observation submitted successfully!",
  "data": {
    "observation_id": 42,
    "project_id": 23,
    "student_name": "Alice Johnson",
    "field_data": [
      {
        "field_id": 15,
        "field_value": "Blue Jay"
      },
      {
        "field_id": 16,
        "field_value": "Sunny"
      },
      {
        "field_id": 17,
        "field_value": "5"
      }
    ]
  }
}
```

Failure Response (400 - Invalid Data):

```
{
  "success": false,
  "error": "field_data must be an object with field_id as keys."
}
```

Failure Response (404 - Project Not Found):

```
{
  "success": false,
  "error": "Project not found.",
  "message": "No project with ID 23 exists."
}
```

</blockquote>

**Get All Observations for a Project**

<blockquote>

_Retrieves all associated observations for a specific project._

Endpoint:

'GET /api/projects/{project_id}/observations'

JSON Request Requirements:

* project_id

CURL Example:

```
curl https://csafk-277534145495.us-east4.run.app/api/projects/23/observations
```

Success Response (200):

```
{
  "success": true,
  "data": [
    {
      "observation_id": 42,
      "project_id": 23,
      "student_name": "Alice Johnson",
      "field_data": [
        {
          "data_id": 101,
          "field_id": 15,
          "field_value": "Blue Jay",
          "field_name": "bird_species",
          "field_label": "Bird Species"
        },
        {
          "data_id": 102,
          "field_id": 16,
          "field_value": "Sunny",
          "field_name": "weather",
          "field_label": "Weather Condition"
        }
      ]
    },
    {
      "observation_id": 43,
      "project_id": 23,
      "student_name": "Bob Smith",
      "field_data": [
        {
          "data_id": 103,
          "field_id": 15,
          "field_value": "Cardinal",
          "field_name": "bird_species",
          "field_label": "Bird Species"
        }
      ]
    }
  ]
}
```

Failure Response (404 - Project Not Found:

```
{
  "success": false,
  "error": "Project not found.",
  "message": "No project with ID 23 exists."
}
```

</blockquote>

**Retrieve Specific Observation**

<blockquote>

_Retrieves a single observation._

Endpoint:

'GET /api/projects/{project_id}/observations/{observation_id}'

JSON Request Requirements:

* project_id
* observation_id

CURL Example:

```
curl https://csafk-277534145495.us-east4.run.app/api/projects/23/observations/42
```

Success Response (200):

```
{
  "success": true,
  "data": {
    "observation_id": 42,
    "project_id": 23,
    "student_name": "Alice Johnson",
    "field_data": [
      {
        "data_id": 101,
        "field_id": 15,
        "field_value": "Blue Jay",
        "field_name": "bird_species",
        "field_label": "Bird Species"
      },
      {
        "data_id": 102,
        "field_id": 16,
        "field_value": "Sunny",
        "field_name": "weather",
        "field_label": "Weather Condition"
      }
    ]
  }
}
```

Failure Response (404 - Observation Not Found):

```
{
  "success": false,
  "error": "Observation not found.",
  "message": "No observation with ID 42 exists for this project."
}
```

Failure Response (404 - Project Not Found):

```
{
  "success": false,
  "error": "Project not found.",
  "message": "No project with ID 23 exists."
}
```

</blockquote>

**Update Observation**

<blockquote>

_Updates an observation. Currently requires authentication. Will be revised for student integration._

Endpoint:

'PUT /api/projects/{project_id}/observations/{observation_id}'

JSON Request Requirements:

* project_id
* observation_id
* student_name (optional)
* field_data (optional)

CURL Example:

```
curl -X PUT https://csafk-277534145495.us-east4.run.app/api/projects/23/observations/42 \
  -H "Content-Type: application/json" \
  -H "Cookie: session=SESSION_COOKIE" \
  -d '{
    "student_name": "Alice Johnson (Updated)",
    "field_data": {
      "15": "Blue Jay (Adult)",
      "17": "6"
    }
  }'
```

Success Response (200):

```
{
  "success": true,
  "message": "Observation ID:42 updated successfully.",
  "data": {
    "observation_id": 42,
    "project_id": 23
  }
}
```

Failure Response (400 - Invalid Data):

```
{
  "success": false,
  "error": "field_data must be an object with field_id as keys."
}
```

Failure Response (400 - Incorrect Project):

```
{
  "success": false,
  "error": "Observation does not belong to this project."
}
```

Failure Response (403 - Unauthorized):

```
{
  "success": false,
  "error": "Unauthorized.",
  "message": "You don't have permission to update observations for this project."
}
```

Failure Response (404 - Observation Not Found):

```
{
  "success": false,
  "error": "Observation not found.",
  "message": "No observation with ID 42 exists."
}
```

</blockquote>

**Delete Observation**

<blockquote>

_Deletes an observation. Currently requires authentication, will be revised with "Update Observation" later._

Endpoint:

'DELETE /api/projects/{project_id}/observations/{observation_id}'

JSON Request Requirements:

* project_id
* observation_id

CURL Example:

```
curl -X DELETE https://csafk-277534145495.us-east4.run.app/api/projects/23/observations/42 \
  -H "Cookie: session=SESSION_COOKIE"
```

Success Response (200):

```
{
  "success": true,
  "message": "Observation ID:42 deleted successfully."
}
```

Failure Response (400 - Incorrect Project):

```
{
  "success": false,
  "error": "Observation does not belong to this project."
}
```

Failure Response (403 - Unauthorized):

```
{
  "success": false,
  "error": "Unauthorized.",
  "message": "You don't have permission to delete observations for this project."
}
```

Failure Response (404 - Observation Not Found):

```
{
  "success": false,
  "error": "Observation not found.",
  "message": "No observation with ID 42 exists."
}
```

</blockquote>

**Get Project by Code - Student**

<blockquote>

_Retrieves project information with no authentication required. Used by students in the field app._

Endpoint:

'GET /api/student/project/{project_code}'

JSON Request Requirements:

* project_code

CURL Example:

```
curl https://csafk-277534145495.us-east4.run.app/api/student/project/A82KP0QM
```

Success Response (200):

```
{
  "success": true,
  "data": {
    "project_id": 1,
    "project_code": "A82KP0QM",
    "project_title": "Bumblebee Tracker",
    "project_description": "Track different bumblees you see.",
    "project_instructions": "Use the form below to fill out the type, number, and what time you saw the bumblebee.",
    "fields": [
      {
        "field_id": 15,
        "field_name": "bird_species",
        "field_label": "Bird Species",
        "field_type": "text",
        "field_options": null,
        "field_required": true
      },
      {
        "field_id": 16,
        "field_name": "weather",
        "field_label": "Weather Condition",
        "field_type": "dropdown",
        "field_options": "[\"Sunny\", \"Cloudy\", \"Rainy\", \"Snowy\"]",
        "field_required": false
      }
    ]
  }
}
```

Failure Response (404 - Project Not Found):

```
{
  "success": false,
  "error": "Project not found.",
  "message": "No project with code 'A82KP0QM' exists."
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
