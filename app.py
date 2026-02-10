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
         FE_PRODUCTION_URL
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
    """Initiates Google OAuth flow."""
    scheme = 'https' if os.getenv("FLASK_ENV") == "production" else 'http'
    redirect_uri = url_for('authorize', _external=True, _scheme=scheme)

    # Store the referrer to know where to redirect after auth
    referrer = request.referrer or ''
    session['login_referrer'] = referrer

    return google.authorize_redirect(redirect_uri)


@app.route(f"{API_PREFIX}/authorize")
def authorize():
    """Callback endpoint for Google OAuth."""
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
    """Logs out the current teacher"""
    session.pop('teacher', None)
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    }), 200


@app.route(f"{API_PREFIX}/me", methods=["GET"])
@login_required
def get_current_teacher_info():
    """Returns current authenticated teacher info"""
    return jsonify({
        "success": True,
        "data": session['teacher']
    }), 200


# ==========
# General Endpoints
# ==========

@app.route(f"{API_PREFIX}/status", methods=["GET"])
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

@app.route(f"{API_PREFIX}/projects", methods=["POST"])
@login_required
def create_project():
    try:
        data = request.get_json()
        current_teacher = get_current_teacher()

        if not data:
            return jsonify(ERROR_NO_DATA), 400

        project_code = generate_random_project_code()

        # Use current teacher's ID.
        teacher_id = current_teacher['teacher_id']

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


@app.route(f"{API_PREFIX}/projects/<int:project_id>", methods=["PUT"])
@login_required
def update_project(project_id):
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

        db.session.execute(
            text("DELETE FROM projects WHERE project_id = :project_id"),
            {"project_id": project_id},
        )

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
