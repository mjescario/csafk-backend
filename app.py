from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import random
import string
import os
from dotenv import load_dotenv

# Load environment variables from .env file.
load_dotenv()

# Initialize the Flask app.
app = Flask(__name__)

# ==========
# Database Configuration
# ==========

DB_PASSWORD = os.getenv("PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

# Configure SQLAlchemy (confirm if using Cloud SQL or TCP).
if DB_HOST.startswith('/cloudsql/'):
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+mysqlconnector://root:{DB_PASSWORD}@/{DB_NAME}?unix_socket={DB_HOST}"
    )
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+mysqlconnector://root:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database.
db = SQLAlchemy(app)


# Root endpoint to test Flask is working.
@app.route("/")
def root():
    return "Flask is running!"


# ==========
# Helper Functions
# ==========

def generate_random_project_code():
    """
    Generates a unique 8-character project code for project student access.
    """
    code_length = 8
    characters = string.ascii_uppercase + string.digits
    generated_code = "".join(random.choices(characters, k=code_length))

    # Check to see if it is unique.
    while not unique_project_code_check(generated_code):
        generated_code = "".join(random.choices(characters, k=code_length))

    return generated_code


def unique_project_code_check(code):
    """
    Checks to see if a project code is unique/already exists in the DB.
    """
    result = db.session.execute(
        text("SELECT COUNT(*) FROM projects WHERE project_code = :code"),
        {"code": code},
    )
    count = result.fetchone()[0]
    return count == 0


# ==========
# General Endpoints
# ==========

# ---------
# Name: Retrieve DB Status
# Method: GET
# Endpoint: /status
# Description: Returns if the connection to the DB is successful.
# ----------

@app.route("/api/status", methods=["GET"])
def health_check():
    """Test if database connection is active."""
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({
            "status": "success",
            "message": "Connected to database successfully!"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"Connection Error": str(e)}), 500


# ==========
# Project Management Endpoints
# ==========

# ---------
# Name: Create Project 
# Method: POST
# Endpoint: /projects
# Description: Creates a new project.
# ----------

@app.route("/api/projects", methods=["POST"])
def create_project():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided."
            }), 400

        project_code = generate_random_project_code()

        result = db.session.execute(
            text("""
                INSERT INTO projects
                    (teacher_id, project_code, project_title, project_description, project_instructions)
                VALUES
                    (:teacher_id, :project_code, :project_title, :project_description, :project_instructions)
            """),
            {
                "teacher_id": data.get("teacher_id"),
                "project_code": project_code,
                "project_title": data.get("project_title"),
                "project_description": data.get("project_description"),
                "project_instructions": data.get("project_instructions"),
            },
        )

        project_id = result.lastrowid
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Project created successfully!",
            "data": {
                "project_id": project_id,
                "project_code": project_code,
                "project_title": data.get("project_title"),
                "project_description": data.get("project_description"),
                "project_instructions": data.get("project_instructions"),
            },
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


# ----------
# Name: Update Project
# Method: PUT
# Endpoint: /projects/<int:project_id>
# Description: Updates an existing project's details.
# ----------

@app.route("/api/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided."
            }), 400

        # First check if project exists
        result = db.session.execute(
            text("SELECT project_id FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        if not result.fetchone():
            return jsonify({
                "success": False,
                "error": "Project not found",
                "message": f"No project with ID {project_id} exists."
            }), 404

        # Initialize update_fields and append updated fields.
        update_fields = []
        params = {"project_id": project_id}

        if "project_title" in data:
            update_fields.append("project_title = :project_title")
            params["project_title"] = data["project_title"]

        if "project_description" in data:
            update_fields.append("project_description = :project_description")
            params["project_description"] = data["project_description"]

        if "project_instructions" in data:
            update_fields.append("project_instructions = :project_instructions")
            params["project_instructions"] = data["project_instructions"]

        # Error Response if not valid.
        if not update_fields:
            return jsonify({
                "success": False,
                "error": "No valid fields to update."
            }), 400

        query = f"UPDATE projects SET {', '.join(update_fields)} WHERE project_id = :project_id"

        db.session.execute(text(query), params)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Project ID:{project_id} updated successfully.",
            "data": {
                "project_id": project_id,
                **data
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


# ----------
# Name: Retrieve Project by ID
# Method: GET
# Endpoint: /projects/<int:project_id>
# Description: Retrieves a project by its ID.
# ----------

@app.route("/api/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    try:
        result = db.session.execute(
            text("""
                SELECT project_id, teacher_id, project_code, project_title, project_description, project_instructions
                FROM projects
                WHERE project_id = :project_id
            """),
            {"project_id": project_id},
        )

        project = result.fetchone()

        if not project:
            return jsonify({
                "success": False,
                "error": "Project not found.",
                "message": f"No project with ID #{project_id} exists."
            }), 404

        return jsonify({
            "success": True,
            "data": {
                "project_id": project[0],
                "teacher_id": project[1],
                "project_code": project[2],
                "project_title": project[3],
                "project_description": project[4],
                "project_instructions": project[5],
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


# ----------
# Name: Retrieve Projects by Teacher
# Method: GET
# Endpoint: /users/<int:teacher_id>/projects
# Description: Retrieves a list of projects by teacher_id.
# ----------

@app.route("/api/users/<int:teacher_id>/projects", methods=["GET"])
def get_projects_by_teacher(teacher_id):
    try:
        result = db.session.execute(
            text("""
                SELECT project_id, teacher_id, project_code, project_title, project_description, project_instructions
                FROM projects
                WHERE teacher_id = :teacher_id
                ORDER BY project_id DESC
            """),
            {"teacher_id": teacher_id},
        )

        projects = result.fetchall()

        projects_list = []
        for p in projects:
            projects_list.append({
                "project_id": p[0],
                "teacher_id": p[1],
                "project_code": p[2],
                "project_title": p[3],
                "project_description": p[4],
                "project_instructions": p[5],
            })

        return jsonify({
            "success": True,
            "data": projects_list
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


# ----------
# Name: Delete Project
# Method: DELETE
# Endpoint: /projects/[project_id]
# Description: Deletes a project and all data (fields, observations, etc.).
# ----------

@app.route("/api/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    try:
        result = db.session.execute(
            text("DELETE FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id},
        )

        if result.rowcount == 0:
            return jsonify({
                "success": False,
                "error": "Project not found",
                "message": f"No project with ID {project_id} exists."
            }), 404

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Project ID:{project_id} deleted successfully."
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Flask server started on port {port}.")
    app.run(debug=False, port=port, host="0.0.0.0")
