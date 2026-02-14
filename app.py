from flask import Flask, jsonify, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import text
from authlib.integrations.flask_client import OAuth
from functools import wraps
import random
import string
import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file.
load_dotenv()

# ==========
# Constants
# ==========

LOCALHOST_URL = "http://localhost:5173"
FE_PRODUCTION_URL = "https://citizen-science-app-for-kids-admin.vercel.app"
API_PREFIX = "/api"

# Error message constants.
ERROR_NO_DATA = {"success": False, "error": "No data provided."}
ERROR_AUTH_REQUIRED = {
    "success": False,
    "error": "Authentication required",
    "message": "Please log in to access this resource."
}
ERROR_PROJECT_NOT_FOUND = {
    "success": False,
    "error": "Project not found."
}
ERROR_UNAUTHORIZED = {
    "success": False,
    "error": "Unauthorized."
}
ERROR_NO_FIELDS_TO_UPDATE = {
    "success": False,
    "error": "No valid fields to update."
}

# ==========
# App Initialization
# ==========

# Initialize the Flask app.
app = Flask(__name__)

# Secret key setup for session management.
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24))

# Detect production environment.
production_check = os.getenv("FLASK_ENV") == "production" or os.getenv("K_SERVICE") is not None

# Set cookies.
app.config['SESSION_COOKIE_SECURE'] = production_check
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None' if production_check else 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# CORS configuration.
CORS(app,
     origins=[
         LOCALHOST_URL,
         FE_PRODUCTION_URL,
         "https://www.google.com",
         "https://google.com",
         "NULL",
         "localhost:8081",
         "http://localhost:8081",
         "https://field-app--development.expo.app"
     ],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
     )

# ==========
# Database Configuration
# ==========

DB_PASSWORD = os.getenv("PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")

# Configure SQLAlchemy (confirm if using Cloud SQL or TCP).
if DB_HOST and DB_HOST.startswith('/cloudsql/'):
    # Set up Cloud SQL Proxy connection.
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+mysqlconnector://root:{DB_PASSWORD}@/{DB_NAME}?unix_socket={DB_HOST}"
    )
else:
    # Set up TCP connection for local testing.
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+mysqlconnector://root:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database.
db = SQLAlchemy(app)

# ==========
# OAuth Configuration
# ==========

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


# ==========
# Authentication Decorator
# ==========

def login_required(f):
    """
    Decorator to require authentication for routes.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'teacher' not in session:
            return jsonify(ERROR_AUTH_REQUIRED), 401
        return f(*args, **kwargs)

    return decorated_function


def get_current_teacher():
    """
    Helper function to get current teacher from session.
    """
    return session.get('teacher')


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


def get_or_create_teacher(google_id, email, name):
    """
    Retrieves teacher from database or creates a new one if doesn't exist.
    Returns teacher_id.
    """
    try:
        # Check if teacher exists by google_id.
        result = db.session.execute(
            text("SELECT teacher_id, email, name FROM teachers WHERE google_id = :google_id"),
            {"google_id": google_id}
        )
        teacher = result.fetchone()

        if teacher:
            # Update teacher info if email or name changed.
            db.session.execute(
                text("""
                    UPDATE teachers 
                    SET email = :email, name = :name
                    WHERE google_id = :google_id
                """),
                {"google_id": google_id, "email": email, "name": name}
            )
            db.session.commit()
            # Returns the teacher_id.
            return teacher[0]
        else:
            # Create new teacher.
            result = db.session.execute(
                text("""
                    INSERT INTO teachers (google_id, email, name)
                    VALUES (:google_id, :email, :name)
                """),
                {"google_id": google_id, "email": email, "name": name}
            )
            db.session.commit()
            return result.lastrowid

    except Exception as e:
        db.session.rollback()
        raise e


# ==========
# Authentication Endpoints
# ==========

# Root endpoint to test Flask is working.
@app.route("/")
def root():
    return "Flask is running!"


@app.route(f"{API_PREFIX}/login")
def login():
    """
    Initiates Google OAuth flow.
    """
    scheme = 'https' if os.getenv("FLASK_ENV") == "production" else 'http'
    redirect_uri = url_for('authorize', _external=True, _scheme=scheme)

    # Store the referrer to know where to redirect after auth
    referrer = request.referrer or ''
    session['login_referrer'] = referrer

    return google.authorize_redirect(redirect_uri)


@app.route(f"{API_PREFIX}/authorize")
def authorize():
    """
    Callback endpoint for Google OAuth.
    """
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')

        if user_info:
            # Get or create teacher in database.
            teacher_id = get_or_create_teacher(
                google_id=user_info['sub'],  # Google's unique user ID
                email=user_info['email'],
                name=user_info.get('name', '')
            )

            # Store teacher info in session.
            session.permanent = True
            session['teacher'] = {
                'teacher_id': teacher_id,
                'google_id': user_info['sub'],
                'email': user_info['email'],
                'name': user_info.get('name', '')
            }

            # Added redirect logic.
            referrer = session.pop('login_referrer', '')

            if 'localhost' in referrer or '127.0.0.1' in referrer:
                # Came from local frontend
                frontend_url = LOCALHOST_URL
            else:
                # Came from production frontend or direct link
                frontend_url = FE_PRODUCTION_URL

            return redirect(f"{frontend_url}/auth/success")

        return jsonify({
            "success": False,
            "error": "Failed to get user info"
        }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route(f"{API_PREFIX}/logout", methods=["POST"])
def logout():
    """
    Logs out the current teacher.
    """
    session.pop('teacher', None)
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    }), 200


@app.route(f"{API_PREFIX}/me", methods=["GET"])
@login_required
def get_current_teacher_info():
    """
    Returns current authenticated teacher info.
    """
    return jsonify({
        "success": True,
        "data": session['teacher']
    }), 200


# ==========
# General Endpoints
# ==========

@app.route(f"{API_PREFIX}/status", methods=["GET"])
def health_check():
    """
    Test if database connection is active.
    """
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

@app.route(f"{API_PREFIX}/projects", methods=["POST"])
@login_required
def create_project():
    """
    Creates a new project.
    """
    try:
        data = request.get_json()
        current_teacher = get_current_teacher()

        if not data:
            return jsonify(ERROR_NO_DATA), 400

        # Validate required field
        if not data.get("project_title"):
            return jsonify({
                "success": False,
                "error": "project_title is required."
            }), 400

        project_code = generate_random_project_code()

        # Use current teacher's ID.
        teacher_id = current_teacher['teacher_id']

        # Set defaults for optional fields to avoid NULL values
        project_title = data.get("project_title")
        project_description = data.get("project_description") or ""
        project_instructions = data.get("project_instructions") or ""

        result = db.session.execute(
            text("""
                INSERT INTO projects
                    (teacher_id, project_code, project_title, project_description, project_instructions)
                VALUES
                    (:teacher_id, :project_code, :project_title, :project_description, :project_instructions)
            """),
            {
                "teacher_id": teacher_id,
                "project_code": project_code,
                "project_title": project_title,
                "project_description": project_description,
                "project_instructions": project_instructions,
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
                "project_title": project_title,
                "project_description": project_description,
                "project_instructions": project_instructions,
            },
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


@app.route(f"{API_PREFIX}/projects/<int:project_id>", methods=["PUT"])
@login_required
def update_project(project_id):
    """
    Updates a current project.
    """
    try:
        data = request.get_json()
        current_teacher = get_current_teacher()

        if not data:
            return jsonify(ERROR_NO_DATA), 400

        # Check if project exists and belongs to current teacher.
        result = db.session.execute(
            text("SELECT teacher_id FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        project = result.fetchone()

        if not project:
            error_response = ERROR_PROJECT_NOT_FOUND.copy()
            error_response["message"] = f"No project with ID {project_id} exists."
            return jsonify(error_response), 404

        # Verify ownership.
        if project[0] != current_teacher['teacher_id']:
            error_response = ERROR_UNAUTHORIZED.copy()
            error_response["message"] = "You don't have permission to update this project."
            return jsonify(error_response), 403

        # Initialize update_fields and params using a loop over approved fields.
        project_fields = ["project_title", "project_description", "project_instructions"]
        update_fields = []
        params = {"project_id": project_id}

        for field in data:
            if field in project_fields:
                update_fields.append(f"{field} = :{field}")
                params[field] = data[field]

        # Error Response if not valid.
        if not update_fields:
            return jsonify(ERROR_NO_FIELDS_TO_UPDATE), 400

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


@app.route(f"{API_PREFIX}/projects/<int:project_id>", methods=["GET"])
@login_required
def get_project(project_id):
    """
    Retrieves a project.
    """
    try:
        current_teacher = get_current_teacher()

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
            error_response = ERROR_PROJECT_NOT_FOUND.copy()
            error_response["message"] = f"No project with ID #{project_id} exists."
            return jsonify(error_response), 404

        # Verify ownership.
        if project[1] != current_teacher['teacher_id']:
            error_response = ERROR_UNAUTHORIZED.copy()
            error_response["message"] = "You don't have permission to view this project."
            return jsonify(error_response), 403

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


@app.route(f"{API_PREFIX}/users/<int:teacher_id>/projects", methods=["GET"])
@login_required
def get_projects_by_teacher(teacher_id):
    """
    Retrieve list of projects by teacher_id.
    """
    try:
        current_teacher = get_current_teacher()

        # Restrict teachers into viewing their own projects.
        if teacher_id != current_teacher['teacher_id']:
            error_response = ERROR_UNAUTHORIZED.copy()
            error_response["message"] = "You can only view your own projects."
            return jsonify(error_response), 403

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


@app.route(f"{API_PREFIX}/projects/<int:project_id>", methods=["DELETE"])
@login_required
def delete_project(project_id):
    """
    Deletes a project. Must be logged in and authorized as project creator.
    Also deletes all associated observations, observation_data, and fields.
    """
    try:
        current_teacher = get_current_teacher()

        # Check if project exists and belongs to current teacher.
        result = db.session.execute(
            text("SELECT teacher_id FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        project = result.fetchone()

        if not project:
            error_response = ERROR_PROJECT_NOT_FOUND.copy()
            error_response["message"] = f"No project with ID {project_id} exists."
            return jsonify(error_response), 404

        # Verify ownership.
        if project[0] != current_teacher['teacher_id']:
            error_response = ERROR_UNAUTHORIZED.copy()
            error_response["message"] = "You don't have permission to delete this project."
            return jsonify(error_response), 403

        # Delete observation_data for all observations in this project.
        db.session.execute(
            text("""
                DELETE FROM observation_data 
                WHERE observation_id IN (
                    SELECT observation_id FROM observations WHERE project_id = :project_id
                )
            """),
            {"project_id": project_id}
        )

        # Delete observations for this project.
        db.session.execute(
            text("DELETE FROM observations WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        # Delete fields for this project.
        db.session.execute(
            text("DELETE FROM project_fields WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        # Finally delete the project.
        db.session.execute(
            text("DELETE FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Project ID:{project_id} deleted successfully."
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


# ==========
# Student Access Endpoints
# ==========

@app.route(f"{API_PREFIX}/student/project/<project_code>", methods=["GET"])
def get_project_by_code(project_code):
    """
    Retrieves public project information for students using project code.
    Does not require authentication - students access via project code.
    Returns limited project info and associated fields for the observation form.
    """
    try:
        # Get project basic info.
        result = db.session.execute(
            text("""
                SELECT project_id, project_code, project_title, project_description, project_instructions
                FROM projects
                WHERE project_code = :project_code
            """),
            {"project_code": project_code},
        )

        project = result.fetchone()

        if not project:
            return jsonify({
                "success": False,
                "error": "Project not found.",
                "message": f"No project with code '{project_code}' exists."
            }), 404

        project_id = project[0]

        # Get all fields for this project.
        fields_result = db.session.execute(
            text("""
                SELECT field_id, field_name, field_label, field_type, field_options, field_required
                FROM project_fields
                WHERE project_id = :project_id
                ORDER BY field_id ASC
            """),
            {"project_id": project_id},
        )

        fields = fields_result.fetchall()

        fields_list = []
        for f in fields:
            fields_list.append({
                "field_id": f[0],
                "field_name": f[1],
                "field_label": f[2],
                "field_type": f[3],
                "field_options": f[4],
                "field_required": bool(f[5]),
            })

        return jsonify({
            "success": True,
            "data": {
                "project_id": project[0],
                "project_code": project[1],
                "project_title": project[2],
                "project_description": project[3],
                "project_instructions": project[4],
                "fields": fields_list
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


# ==========
# Field Management Endpoints
# ==========

@app.route(f"{API_PREFIX}/projects/<int:project_id>/fields", methods=["POST"])
@login_required
def add_field(project_id):
    """
    Add a new field to a project.
    """
    try:
        data = request.get_json()
        current_teacher = get_current_teacher()

        if not data:
            return jsonify(ERROR_NO_DATA), 400

        # Check if project exists and belongs to current teacher.
        result = db.session.execute(
            text("SELECT teacher_id FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        project = result.fetchone()

        if not project:
            error_response = ERROR_PROJECT_NOT_FOUND.copy()
            error_response["message"] = f"No project with ID {project_id} exists."
            return jsonify(error_response), 404

        # Verify ownership.
        if project[0] != current_teacher['teacher_id']:
            error_response = ERROR_UNAUTHORIZED.copy()
            error_response["message"] = "You don't have permission to add fields to this project."
            return jsonify(error_response), 403

        # Validate required fields.
        if not data.get("field_name") or not data.get("field_type"):
            return jsonify({
                "success": False,
                "error": "field_name and field_type are required."
            }), 400

        # Set defaults for optional fields
        field_label = data.get("field_label") or data.get("field_name")
        field_required = data.get("is_required", False) or data.get("field_required", False)

        # Insert the field.
        result = db.session.execute(
            text("""
                INSERT INTO project_fields
                    (project_id, field_name, field_label, field_type, field_options, field_required)
                VALUES
                    (:project_id, :field_name, :field_label, :field_type, :field_options, :field_required)
            """),
            {
                "project_id": project_id,
                "field_name": data.get("field_name"),
                "field_label": field_label,
                "field_type": data.get("field_type"),
                "field_options": data.get("field_options"),
                "field_required": field_required,
            },
        )

        field_id = result.lastrowid
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Field added successfully!",
            "data": {
                "field_id": field_id,
                "project_id": project_id,
                "field_name": data.get("field_name"),
                "field_label": field_label,
                "field_type": data.get("field_type"),
                "field_options": data.get("field_options"),
                "field_required": field_required,
            },
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


@app.route(f"{API_PREFIX}/projects/<int:project_id>/fields", methods=["GET"])
@login_required
def get_fields(project_id):
    """
    Retrieve all fields for a project.
    """
    try:
        current_teacher = get_current_teacher()

        # Check if project exists and belongs to current teacher.
        result = db.session.execute(
            text("SELECT teacher_id FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        project = result.fetchone()

        if not project:
            error_response = ERROR_PROJECT_NOT_FOUND.copy()
            error_response["message"] = f"No project with ID {project_id} exists."
            return jsonify(error_response), 404

        # Verify ownership.
        if project[0] != current_teacher['teacher_id']:
            error_response = ERROR_UNAUTHORIZED.copy()
            error_response["message"] = "You don't have permission to view fields for this project."
            return jsonify(error_response), 403

        # Get all fields for the project.
        result = db.session.execute(
            text("""
                SELECT field_id, project_id, field_name, field_label, field_type, field_options, field_required
                FROM project_fields
                WHERE project_id = :project_id
                ORDER BY field_id ASC
            """),
            {"project_id": project_id},
        )

        fields = result.fetchall()

        fields_list = []
        for f in fields:
            fields_list.append({
                "field_id": f[0],
                "project_id": f[1],
                "field_name": f[2],
                "field_label": f[3],
                "field_type": f[4],
                "field_options": f[5],
                "field_required": bool(f[6]),
            })

        return jsonify({
            "success": True,
            "data": fields_list
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


@app.route(f"{API_PREFIX}/projects/<int:project_id>/fields/<int:field_id>", methods=["PUT"])
@login_required
def update_field(project_id, field_id):
    """
    Update a field.
    """
    try:
        data = request.get_json()
        current_teacher = get_current_teacher()

        if not data:
            return jsonify(ERROR_NO_DATA), 400

        # Check if project exists and belongs to current teacher.
        result = db.session.execute(
            text("SELECT teacher_id FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        project = result.fetchone()

        if not project:
            error_response = ERROR_PROJECT_NOT_FOUND.copy()
            error_response["message"] = f"No project with ID {project_id} exists."
            return jsonify(error_response), 404

        # Verify ownership.
        if project[0] != current_teacher['teacher_id']:
            error_response = ERROR_UNAUTHORIZED.copy()
            error_response["message"] = "You don't have permission to update fields for this project."
            return jsonify(error_response), 403

        # Check if field exists and belongs to this project.
        result = db.session.execute(
            text("SELECT project_id FROM project_fields WHERE field_id = :field_id"),
            {"field_id": field_id}
        )

        field = result.fetchone()

        if not field:
            return jsonify({
                "success": False,
                "error": "Field not found.",
                "message": f"No field with ID {field_id} exists."
            }), 404

        if field[0] != project_id:
            return jsonify({
                "success": False,
                "error": "Field does not belong to this project."
            }), 400

        # Initialize update_fields and params using a loop over approved fields.
        # Map API field names to database column names
        field_mapping = {
            "field_name": "field_name",
            "field_label": "field_label",
            "field_type": "field_type",
            "field_options": "field_options",
            "is_required": "field_required",
            "field_required": "field_required"
        }

        update_fields = []
        params = {"field_id": field_id}

        for api_field, db_field in field_mapping.items():
            if api_field in data:
                update_fields.append(f"{db_field} = :{db_field}")
                params[db_field] = data[api_field]

        # Error Response if not valid.
        if not update_fields:
            return jsonify(ERROR_NO_FIELDS_TO_UPDATE), 400

        query = f"UPDATE project_fields SET {', '.join(update_fields)} WHERE field_id = :field_id"

        db.session.execute(text(query), params)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Field ID:{field_id} updated successfully.",
            "data": {
                "field_id": field_id,
                "project_id": project_id,
                **data
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


@app.route(f"{API_PREFIX}/projects/<int:project_id>/fields/<int:field_id>", methods=["DELETE"])
@login_required
def delete_field(project_id, field_id):
    """
    Delete a field.
    """
    try:
        current_teacher = get_current_teacher()

        # Check if project exists and belongs to current teacher.
        result = db.session.execute(
            text("SELECT teacher_id FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        project = result.fetchone()

        if not project:
            error_response = ERROR_PROJECT_NOT_FOUND.copy()
            error_response["message"] = f"No project with ID {project_id} exists."
            return jsonify(error_response), 404

        # Verify ownership.
        if project[0] != current_teacher['teacher_id']:
            error_response = ERROR_UNAUTHORIZED.copy()
            error_response["message"] = "You don't have permission to delete fields for this project."
            return jsonify(error_response), 403

        # Check if field exists and belongs to this project.
        result = db.session.execute(
            text("SELECT project_id FROM project_fields WHERE field_id = :field_id"),
            {"field_id": field_id}
        )

        field = result.fetchone()

        if not field:
            return jsonify({
                "success": False,
                "error": "Field not found.",
                "message": f"No field with ID {field_id} exists."
            }), 404

        if field[0] != project_id:
            return jsonify({
                "success": False,
                "error": "Field does not belong to this project."
            }), 400

        db.session.execute(
            text("DELETE FROM project_fields WHERE field_id = :field_id"),
            {"field_id": field_id},
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Field ID:{field_id} deleted successfully."
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


# ==========
# Observation Management Endpoints
# ==========

@app.route(f"{API_PREFIX}/projects/<int:project_id>/observations", methods=["POST"])
def submit_observation(project_id):
    """
    Submit a new observation for a project using project_id.
    No authentication required - accessible by both teachers and students.
    Creates an observation record and associated observation_data records.
    Stores values in appropriate typed columns based on field type.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify(ERROR_NO_DATA), 400

        # Check if project exists.
        result = db.session.execute(
            text("SELECT project_id FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        project = result.fetchone()

        if not project:
            error_response = ERROR_PROJECT_NOT_FOUND.copy()
            error_response["message"] = f"No project with ID {project_id} exists."
            return jsonify(error_response), 404

        # Extract student_name and field_data from request.
        student_name = data.get("student_name", "")
        field_data = data.get("field_data", {})

        if not isinstance(field_data, dict):
            return jsonify({
                "success": False,
                "error": "field_data must be an object with field_id as keys."
            }), 400

        # Create the observation record.
        result = db.session.execute(
            text("""
                INSERT INTO observations (project_id, student_name)
                VALUES (:project_id, :student_name)
            """),
            {
                "project_id": project_id,
                "student_name": student_name
            }
        )

        observation_id = result.lastrowid

        # Insert observation_data for each field.
        observation_data_list = []
        for field_id_str, field_value in field_data.items():
            try:
                field_id = int(field_id_str)
            except ValueError:
                continue

            # Get field info to determine type.
            field_check = db.session.execute(
                text("""
                    SELECT field_id, field_type 
                    FROM project_fields 
                    WHERE field_id = :field_id AND project_id = :project_id
                """),
                {"field_id": field_id, "project_id": project_id}
            )

            field_info = field_check.fetchone()

            if field_info:
                field_type = field_info[1]

                # Determine which column to use based on field type.
                value_text = None
                value_number = None
                value_date = None
                value_boolean = None

                # Map field types to storage columns.
                numeric_types = ['number']
                date_types = ['date']
                boolean_types = ['checkbox']
                multiselect_types = ['multiselect']
                text_types = ['text', 'textarea', 'radio', 'time']

                if field_type in numeric_types:
                    try:
                        value_number = float(field_value) if field_value not in [None, ""] else None
                    except (ValueError, TypeError):
                        value_number = None

                elif field_type in date_types:
                    try:
                        # Validate date format.
                        from datetime import datetime
                        if field_value:
                            datetime.strptime(str(field_value), "%Y-%m-%d")
                            value_date = str(field_value)
                    except (ValueError, TypeError):
                        value_date = None

                elif field_type in boolean_types:
                    # Convert to boolean.
                    value_boolean = str(field_value).lower() in ['true', '1', 'yes', 'on'] if field_value else False

                elif field_type in multiselect_types:
                    # Store as JSON array.
                    import json
                    if isinstance(field_value, list):
                        value_text = json.dumps(field_value)
                    elif isinstance(field_value, str):
                        # If already JSON string, validate and store.
                        try:
                            json.loads(field_value)
                            value_text = field_value
                        except:
                            # If comma-separated, convert to JSON array.
                            value_text = json.dumps([v.strip() for v in field_value.split(',')])
                    else:
                        value_text = json.dumps([])

                else:
                    value_text = str(field_value) if field_value is not None else ""

                # Store in field_value for backward compatibility.
                field_value_str = str(field_value) if field_value is not None else ""

                db.session.execute(
                    text("""
                        INSERT INTO observation_data 
                            (observation_id, field_id, field_value, value_text, value_number, value_date, value_boolean)
                        VALUES 
                            (:observation_id, :field_id, :field_value, :value_text, :value_number, :value_date, :value_boolean)
                    """),
                    {
                        "observation_id": observation_id,
                        "field_id": field_id,
                        "field_value": field_value_str,
                        "value_text": value_text,
                "value_number": value_number,
                        "value_date": value_date,
                        "value_boolean": value_boolean
                    }
                )
                observation_data_list.append({
                    "field_id": field_id,
                    "field_value": field_value_str
                })

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Observation submitted successfully!",
            "data": {
                "observation_id": observation_id,
                "project_id": project_id,
                "student_name": student_name,
                "field_data": observation_data_list
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


@app.route(f"{API_PREFIX}/projects/<int:project_id>/observations", methods=["GET"])
def get_all_observations(project_id):
    """
    Retrieve all observations for a project with their associated data.
    No authentication required - accessible by both teachers and students.
    """
    try:
        # Check if project exists.
        result = db.session.execute(
            text("SELECT project_id FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        project = result.fetchone()

        if not project:
            error_response = ERROR_PROJECT_NOT_FOUND.copy()
            error_response["message"] = f"No project with ID {project_id} exists."
            return jsonify(error_response), 404

        # Get all observations for the project.
        result = db.session.execute(
            text("""
                SELECT observation_id, project_id, student_name
                FROM observations
                WHERE project_id = :project_id
                ORDER BY observation_id DESC
            """),
            {"project_id": project_id}
        )

        observations = result.fetchall()

        observations_list = []
        for obs in observations:
            observation_id = obs[0]

            # Get observation_data for this observation.
            data_result = db.session.execute(
                text("""
                    SELECT od.data_id, od.field_id, od.field_value, pf.field_name, pf.field_label
                    FROM observation_data od
                    JOIN project_fields pf ON od.field_id = pf.field_id
                    WHERE od.observation_id = :observation_id
                    ORDER BY od.field_id ASC
                """),
                {"observation_id": observation_id}
            )

            field_data = []
            for data in data_result.fetchall():
                field_data.append({
                    "data_id": data[0],
                    "field_id": data[1],
                    "field_value": data[2],
                    "field_name": data[3],
                    "field_label": data[4]
                })

            observations_list.append({
                "observation_id": obs[0],
                "project_id": obs[1],
                "student_name": obs[2],
                "field_data": field_data
            })

        return jsonify({
            "success": True,
            "data": observations_list
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


@app.route(f"{API_PREFIX}/projects/<int:project_id>/observations/<int:observation_id>", methods=["GET"])
def get_observation(project_id, observation_id):
    """
    Get a specific observation with its data.
    No authentication required - accessible by both teachers and students.
    """
    try:
        # Check if project exists.
        result = db.session.execute(
            text("SELECT project_id FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        project = result.fetchone()

        if not project:
            error_response = ERROR_PROJECT_NOT_FOUND.copy()
            error_response["message"] = f"No project with ID {project_id} exists."
            return jsonify(error_response), 404

        # Get the observation.
        result = db.session.execute(
            text("""
                SELECT observation_id, project_id, student_name
                FROM observations
                WHERE observation_id = :observation_id AND project_id = :project_id
            """),
            {"observation_id": observation_id, "project_id": project_id}
        )

        observation = result.fetchone()

        if not observation:
            return jsonify({
                "success": False,
                "error": "Observation not found.",
                "message": f"No observation with ID {observation_id} exists for this project."
            }), 404

        # Get observation_data.
        data_result = db.session.execute(
            text("""
                SELECT od.data_id, od.field_id, od.field_value, pf.field_name, pf.field_label
                FROM observation_data od
                JOIN project_fields pf ON od.field_id = pf.field_id
                WHERE od.observation_id = :observation_id
                ORDER BY od.field_id ASC
            """),
            {"observation_id": observation_id}
        )

        field_data = []
        for data in data_result.fetchall():
            field_data.append({
                "data_id": data[0],
                "field_id": data[1],
                "field_value": data[2],
                "field_name": data[3],
                "field_label": data[4]
            })

        return jsonify({
            "success": True,
            "data": {
                "observation_id": observation[0],
                "project_id": observation[1],
                "student_name": observation[2],
                "field_data": field_data
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


@app.route(f"{API_PREFIX}/projects/<int:project_id>/observations/<int:observation_id>", methods=["PUT"])
def update_observation(project_id, observation_id):
    """
    Update an observation and its field data.
    """
    try:
        data = request.get_json()
        current_teacher = get_current_teacher()

        if not data:
            return jsonify(ERROR_NO_DATA), 400

        # Check if project exists and belongs to current teacher.
        result = db.session.execute(
            text("SELECT teacher_id FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        project = result.fetchone()

        if not project:
            error_response = ERROR_PROJECT_NOT_FOUND.copy()
            error_response["message"] = f"No project with ID {project_id} exists."
            return jsonify(error_response), 404

        # Verify ownership.
        if project[0] != current_teacher['teacher_id']:
            error_response = ERROR_UNAUTHORIZED.copy()
            error_response["message"] = "You don't have permission to update observations for this project."
            return jsonify(error_response), 403

        # Check if observation exists and belongs to this project.
        result = db.session.execute(
            text("SELECT project_id FROM observations WHERE observation_id = :observation_id"),
            {"observation_id": observation_id}
        )

        observation = result.fetchone()

        if not observation:
            return jsonify({
                "success": False,
                "error": "Observation not found.",
                "message": f"No observation with ID {observation_id} exists."
            }), 404

        if observation[0] != project_id:
            return jsonify({
                "success": False,
                "error": "Observation does not belong to this project."
            }), 400

        # Update student_name if provided.
        if "student_name" in data:
            db.session.execute(
                text("""
                    UPDATE observations
                    SET student_name = :student_name
                    WHERE observation_id = :observation_id
                """),
                {
                    "student_name": data.get("student_name", ""),
                    "observation_id": observation_id
                }
            )

        # Update field_data if provided.
        if "field_data" in data:
            field_data = data.get("field_data", {})

            if not isinstance(field_data, dict):
                return jsonify({
                    "success": False,
                    "error": "field_data must be an object with field_id as keys."
                }), 400

            for field_id_str, field_value in field_data.items():
                try:
                    field_id = int(field_id_str)
                except ValueError:
                    continue

                # Get field info to determine type.
                field_check = db.session.execute(
                    text("""
                        SELECT field_id, field_type 
                        FROM project_fields 
                        WHERE field_id = :field_id AND project_id = :project_id
                    """),
                    {"field_id": field_id, "project_id": project_id}
                )

                field_info = field_check.fetchone()

                if field_info:
                    field_type = field_info[1]

                    # Determine which column to use based on field type.
                    value_text = None
                    value_number = None
                    value_date = None
                    value_boolean = None

                    numeric_types = ['number']
                    date_types = ['date']
                    boolean_types = ['checkbox']
                    multiselect_types = ['multiselect']
                    text_types = ['text', 'textarea', 'radio', 'time']

                    if field_type in numeric_types:
                        try:
                            value_number = float(field_value) if field_value not in [None, ""] else None
                        except (ValueError, TypeError):
                            value_number = None

                    elif field_type in date_types:
                        try:
                            from datetime import datetime
                            if field_value:
                                datetime.strptime(str(field_value), "%Y-%m-%d")
                                value_date = str(field_value)
                        except (ValueError, TypeError):
                            value_date = None

                    elif field_type in boolean_types:
                        value_boolean = str(field_value).lower() in ['true', '1', 'yes', 'on'] if field_value else False

                    elif field_type in multiselect_types:
                        import json
                        if isinstance(field_value, list):
                            value_text = json.dumps(field_value)
                        elif isinstance(field_value, str):
                            try:
                                json.loads(field_value)
                                value_text = field_value
                            except:
                                value_text = json.dumps([v.strip() for v in field_value.split(',')])
                        else:
                            value_text = json.dumps([])

                    else:
                        value_text = str(field_value) if field_value is not None else ""

                    field_value_str = str(field_value) if field_value is not None else ""

                    # Check if data entry exists.
                    existing_data = db.session.execute(
                        text("""
                            SELECT data_id FROM observation_data
                            WHERE observation_id = :observation_id AND field_id = :field_id
                        """),
                        {"observation_id": observation_id, "field_id": field_id}
                    )

                    if existing_data.fetchone():
                        # Update existing observation.
                        db.session.execute(
                            text("""
                                UPDATE observation_data
                                SET field_value = :field_value,
                                    value_text = :value_text,
                                    value_number = :value_number,
                                    value_date = :value_date,
                                    value_boolean = :value_boolean
                                WHERE observation_id = :observation_id AND field_id = :field_id
                            """),
                            {
                                "field_value": field_value_str,
                                "value_text": value_text,
                                "value_number": value_number,
                                "value_date": value_date,
                                "value_boolean": value_boolean,
                                "observation_id": observation_id,
                                "field_id": field_id
                            }
                        )
                    else:
                        # Insert new observation.
                        db.session.execute(
                            text("""
                                INSERT INTO observation_data 
                                    (observation_id, field_id, field_value, value_text, value_number, value_date, value_boolean)
                                VALUES 
                                    (:observation_id, :field_id, :field_value, :value_text, :value_number, :value_date, :value_boolean)
                            """),
                            {
                                "observation_id": observation_id,
                                "field_id": field_id,
                                "field_value": field_value_str,
                                "value_text": value_text,
                                "value_number": value_number,
                                "value_date": value_date,
                                "value_boolean": value_boolean
                            }
                        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Observation ID:{observation_id} updated successfully.",
            "data": {
                "observation_id": observation_id,
                "project_id": project_id
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


@app.route(f"{API_PREFIX}/projects/<int:project_id>/observations/<int:observation_id>", methods=["DELETE"])
@login_required
def delete_observation(project_id, observation_id):
    """
    Delete an observation and its associated data.
    """
    try:
        current_teacher = get_current_teacher()

        # Check if project exists and belongs to current teacher.
        result = db.session.execute(
            text("SELECT teacher_id FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id}
        )

        project = result.fetchone()

        if not project:
            error_response = ERROR_PROJECT_NOT_FOUND.copy()
            error_response["message"] = f"No project with ID {project_id} exists."
            return jsonify(error_response), 404

        # Verify ownership.
        if project[0] != current_teacher['teacher_id']:
            error_response = ERROR_UNAUTHORIZED.copy()
            error_response["message"] = "You don't have permission to delete observations for this project."
            return jsonify(error_response), 403

        # Check if observation exists and belongs to this project.
        result = db.session.execute(
            text("SELECT project_id FROM observations WHERE observation_id = :observation_id"),
            {"observation_id": observation_id}
        )

        observation = result.fetchone()

        if not observation:
            return jsonify({
                "success": False,
                "error": "Observation not found.",
                "message": f"No observation with ID {observation_id} exists."
            }), 404

        if observation[0] != project_id:
            return jsonify({
                "success": False,
                "error": "Observation does not belong to this project."
            }), 400

        # Delete observation_data first (foreign key constraint).
        db.session.execute(
            text("DELETE FROM observation_data WHERE observation_id = :observation_id"),
            {"observation_id": observation_id}
        )

        # Delete observation.
        db.session.execute(
            text("DELETE FROM observations WHERE observation_id = :observation_id"),
            {"observation_id": observation_id}
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Observation ID:{observation_id} deleted successfully."
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"Server Error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Flask server started on port {port}.")
    app.run(debug=False, port=port, host="0.0.0.0")