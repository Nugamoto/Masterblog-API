import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
from passlib.hash import pbkdf2_sha256

from helpers import (
    load_json,
    save_json,
    validate_post_data,
    find_post_by_id,
    generate_new_id,
    search_posts_by_fields,
    sort_posts,
    paginate_items,
    POSTS_FILE,
    USERS_FILE
)

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per hour"]
)


@app.route("/api/v1/register", methods=["POST"])
@limiter.limit("10 per hour")
def register():
    """
    Register a new user.

    Expects a JSON body with 'username' and 'password'. If either is missing or the username
    already exists, returns a 400 error. On successful registration, the password is hashed
    and the user is added to the users.json file.

    Returns:
        JSON response with a success message and HTTP status code 201 on success, or an error message otherwise.
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    users = load_json(filepath=USERS_FILE)

    if any(user["username"] == username for user in users):
        return jsonify({"error": "Username already exists"}), 400

    hashed_password = pbkdf2_sha256.hash(password)
    users.append({"username": username, "password": hashed_password})

    save_json(users, filepath=USERS_FILE)

    return jsonify({"message": f"User {username} registered successfully"}), 201


@app.route("/api/v1/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    """
    Authenticate a user and issue a JWT token.

    Expects a JSON body with 'username' and 'password'. If the credentials are invalid,
    returns a 401 error. On success, returns a JSON response containing the access token.

    Returns:
        JSON with the access_token on success, or an error message on failure.
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    users = load_json(filepath=USERS_FILE)
    user = next((user for user in users if user["username"] == username), None)

    if not user or not pbkdf2_sha256.verify(password, user["password"]):
        return jsonify({"error": "Invalid username or password"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200


@app.route('/api/v1/posts', methods=['GET', 'POST'])
def handle_posts():
    """
    Retrieve all blog posts or create a new blog post.

    GET:
        Returns a paginated list of posts, with optional sorting if query parameters are provided.
    POST:
        Creates a new blog post. Expects a JSON body with at least 'title' and 'content'.
        Additional fields such as 'date', 'category', 'tags', and 'comments' are optional.
        If 'date' is not provided, the current date is used. The author is determined from the JWT token.
        Requires JWT authentication.

    Returns:
        A JSON response with the requested list of posts for GET requests, or the newly created post for POST requests.
    """
    if request.method == 'POST':
        @jwt_required()
        def protected_create_post():
            all_posts = load_json(filepath=POSTS_FILE)
            new_post = request.get_json()

            missing_data = validate_post_data(new_post)
            if missing_data:
                return jsonify({"error": f"Invalid data. Data requires {missing_data}"}), 400

            if 'date' not in new_post or not new_post['date']:
                new_post["date"] = datetime.now().strftime("%Y-%m-%d")
            new_post.setdefault("category", "")
            new_post.setdefault("tags", [])
            new_post.setdefault("comments", [])

            new_post["id"] = generate_new_id(all_posts)
            new_post["author"] = get_jwt_identity()

            all_posts.append(new_post)
            save_json(all_posts, filepath=POSTS_FILE)
            return jsonify(new_post), 201

        return protected_create_post()

    posts = load_json(filepath=POSTS_FILE)

    paginated_items, error_response, is_error = paginate_items(posts)
    if is_error:
        return error_response

    required_fields = ["id", "title", "content", "author", "date", "category", "comments", "tags"]
    field_to_sort = request.args.get("sort", "").lower()
    if field_to_sort and field_to_sort not in required_fields:
        return jsonify({"error": f"'{field_to_sort}' is not a valid field to sort. Try: {required_fields}"}), 400

    required_direction = ["asc", "desc"]
    sort_direction = request.args.get("direction", "").lower()
    if sort_direction and sort_direction not in required_direction:
        return jsonify(
            {"error": f"'{sort_direction}' is not a valid direction to sort. Try: {required_direction}"}), 400

    if not field_to_sort and sort_direction:
        return jsonify({"error": f"'sort'-parameter is required. Try: {required_fields}"}), 400

    if field_to_sort:
        sorted_posts = sort_posts(posts, field_to_sort, sort_direction)
    else:
        sorted_posts = posts

    paginated_items, error_response, is_error = paginate_items(sorted_posts)
    if is_error:
        return error_response
    return jsonify(paginated_items)


@app.route('/api/v1/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    """
    Delete a blog post by its ID.

    Requires JWT authentication. Only the post's author (as determined from the JWT token)
    is allowed to delete the post.

    Args:
        post_id (int): The unique identifier of the post to delete.

    Returns:
        A JSON response with a success message on deletion or an error message if not authorized or not found.
    """
    posts = load_json(filepath=POSTS_FILE)
    post = find_post_by_id(post_id, posts)

    if not post:
        return jsonify({"error": f"Post with id {post_id} not found."}), 404

    current_user = get_jwt_identity()
    if post.get("author") != current_user:
        return jsonify({"error": "You are not authorized to delete this post."}), 403

    posts.remove(post)
    save_json(posts, filepath=POSTS_FILE)
    return jsonify({"message": f"Post with id {post_id} has been deleted successfully."}), 200


@app.route('/api/v1/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    """
    Update an existing blog post by its ID.

    Requires JWT authentication. Expects a JSON body with updated post data.
    The 'author' field, if provided, is ignored (the author is determined from the JWT token).
    If a 'date' is provided, it must be in the format YYYY-MM-DD.
    Only the author of the post is allowed to update it.

    Args:
        post_id (int): The unique identifier of the post to update.

    Returns:
        The updated post as JSON on success, or an error message on failure.
    """
    posts = load_json(filepath=POSTS_FILE)
    new_post_data = request.get_json()
    missing_data = validate_post_data(new_post_data)
    if missing_data:
        return jsonify({"error": f"Invalid data. Data requires {missing_data}"}), 400

    post = find_post_by_id(post_id, posts)
    if not post:
        return jsonify({"error": f"Post with id {post_id} not found."}), 404

    current_user = get_jwt_identity()
    if post.get("author") != current_user:
        return jsonify({"error": "You are not authorized to update this post."}), 403

    if "author" in new_post_data:
        del new_post_data["author"]

    if "date" in new_post_data:
        try:
            datetime.strptime(new_post_data["date"], "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Date must be in format YYYY-MM-DD"}), 400

    post.update(new_post_data)
    save_json(posts, filepath=POSTS_FILE)
    return jsonify(post), 200


@app.route('/api/v1/posts/search')
def search_post():
    """
    Search for blog posts using various fields.

    Accepts optional query parameters: title, content, author, date, category, and tag.
    Returns a paginated list of posts that match any of the provided search criteria.

    Returns:
        A JSON array of posts that match the search criteria.
    """
    title_term = request.args.get('title', '')
    content_term = request.args.get('content', '')
    author_term = request.args.get('author', '')
    date_term = request.args.get('date', '')
    category_term = request.args.get('category', '')
    tag_term = request.args.get('tag', '')

    posts = load_json(filepath=POSTS_FILE)
    results = search_posts_by_fields(title_term, content_term, author_term, date_term, category_term, tag_term, posts)

    paginated_items, error_response, is_error = paginate_items(results)
    if is_error:
        return error_response
    return jsonify(paginated_items)


@app.route('/api/v1/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    """
    Add a comment to a blog post.

    Requires JWT authentication. Expects a JSON body with a 'text' field.
    The comment's author is derived from the JWT token, and the current timestamp is added.

    Args:
        post_id (int): The unique identifier of the post to which the comment is added.

    Returns:
        The updated post (with the new comment) as JSON on success, or an error message on failure.
    """
    posts = load_json(filepath=POSTS_FILE)
    post = find_post_by_id(post_id, posts)
    if not post:
        return jsonify({"error": f"Post with id {post_id} not found."}), 404

    new_comment = request.get_json()
    if "text" not in new_comment:
        return jsonify({"error": "Comment must include 'text'"}), 400

    new_comment_data = {
        "author": get_jwt_identity(),
        "text": new_comment["text"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    post.setdefault("comments", []).append(new_comment_data)
    save_json(posts, filepath=POSTS_FILE)
    return jsonify(post), 201


SWAGGER_URL = "/api/docs"
API_URL = "/static/masterblog.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "Masterblog API"}
)

app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
