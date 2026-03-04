Geolocation Implementation Documentation

Backend has been updated to log geolocation (longitude and latitude coordinates) when a student submits an observation. Location support is optional and students must authorize location permissions via the field app.

There are three primary affected endpoints:

* Submit Observation
* Get Observation
* Update Observation

Additionally, the CSV has been adjusted to export the location values as well.

To utilize, revise the following endpoints:

**Submit Observation**

<blockquote>

_Submits a new observation for a project. Does not require authentication._

Endpoint:

'POST /api/projects/{project_id}/observations'

JSON Request Requirements:

* project_id
* student_name (optional)
* latitude (optional)
* longitude (optional)
* field_data

CURL Example:

```
curl -X POST https://csafk-277534145495.us-east4.run.app/api/projects/23/observations \
  -H "Content-Type: application/json" \
  -d '{
    "student_name": "Alice Johnson",
    "latitude": 45.5231,
    "longitude": -122.6765,
    "field_data": {
      "15": "Blue Jay",
      "16": "Sunny",
      "17": "5"
    }
  }'
```

** Note that multiselect values should be submitted as a JSON array:

```
"field_data": {
  "18": ["Forest", "Wetland"]
}
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
    "latitude": 45.5231,
    "longitude": -122.6765,
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

Here is the updated information to update a latitude and longitude value. Requires standard authorization (either a logged in teacher that owns the project or a matching student_id) to update.

**Update Observation**

<blockquote>

_Updates an observation. Currently requires authentication. Will be revised for student integration._

Endpoint:

'PUT /api/projects/{project_id}/observations/{observation_id}'

JSON Request Requirements:

* project_id
* observation_id
* student_name (optional)
* latitude (optional)
* longitude (optional)
* field_data (optional)

CURL Example:

```
curl -X PUT https://csafk-277534145495.us-east4.run.app/api/projects/23/observations/42 \
  -H "Content-Type: application/json" \
  -H "Cookie: session=SESSION_COOKIE" \
  -d '{
    "student_name": "Alice Johnson (Updated)",
    "latitude": 45.5232,
    "longitude": -122.6766,
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

Attached here is the updated GET endpoint for retrieving an observation:

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
    "latitude": 45.5231,
    "longitude": -122.6765,
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