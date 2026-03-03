Photo Upload Support Documentation

This functionality allows students to attach photos to their observations. It works by utilizing a separate endpoint that uploads pictures to Google Cloud Storage that is triggered after the initial endpoint submission has been made.

Here is a detailed workflow of how this process works:

1. Student creates a submission and has the option to take or upload a photo.
2. Field app sends the standard POST for the submission and receives the observation_id.
3. If a photo is attached, then POST the image using the observation_id to the photo endpoint.
4. Backend uploads the file to Google Cloud Storage and then appends the photo URL to the observation.

Detailed Photo Endpoint Information:

**Upload Observation Photoe**

<blockquote>

Endpoint allows photo uploads to an associated observation using observation_id. Requires either a teacher or a student with a matching student_id to upload (similar to the update_observation permissions). Endpoint will take a photo, upload it to Google Cloud Storage, and then append the URL to that image to the observation.

Endpoint:

'POST /api/projects/{project_id}/observations/{observation_id}/photo'

Note: Must be a multipart/form-data content-type.

JSON Request Requirements:

* Photo in JPEG, PNG, GIF, or WebP format
* student_id (only required for students to authenticate)

CURL Example:

```
curl -X POST \
  https://your-api-url/api/projects/1/observations/42/photo \
  -F "photo=@/path/to/image.jpg" \
  -F "student_id=abc123"
```

Success Response (200):

```
{
  "success": true,
  "message": "Photo uploaded successfully.",
  "data": {
    "observation_id": 42,
    "photo_url": "https://storage.googleapis.com/citizen-science-photos/observations/testpicture123.jpg"
  }
}
```

Failure Responses:

* 400 - No photo file provided
* 400 - No filename
* 400 - Invalid file type
* 401 - Authentication required (did not provide student_id or teacher's cookie session has expired)
* 403 - Unauthorized (student_id does not match token or teacher doesn't own project)
* 404 - Project not found
* 404 - Observation not found

</blockquote>

Field App Implementation:

Attached are two tutorials that should help with your field app.

* Official Documentation for Expo Image Picker
Link: https://docs.expo.dev/tutorial/image-picker/
Good resource with sample code on the expo-image-picker library needed.

* YouTube Tutorial for Image Upload
Link: https://www.youtube.com/watch?v=uX5E_QFJubU
This tutorial is very comprehensive for what is needed for our platform. It covers selecting pictures, taking pictures with the camera, and around the 6:50ish mark the tutorial goes into detail on how to set up the API call.

NOTE: This worked in my tests locally and on the deployed version. Some factors (like permissions or authorized use of the GCS bucket) may require additional adjustment in the backend. Please contact me with any errors you receive during implementation.

TODO: In addition to this, I need to write an additional endpoint to delete the photo.