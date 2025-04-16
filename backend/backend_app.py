import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from passlib.hash import pbkdf2_sha256

load_dotenv()

app = Flask(__name__)

CORS(app)  # This will enable CORS for all routes (Cross-Origin Resource Sharing)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

jwt = JWTManager(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per hour"]
)

USERS = []  # Dummy-Speicher für Benutzer (später kann hier eine DB hin)

POSTS = [
    {
        "id": 1,
        "title": "First post",
        "content": "This is the first post.",
        "author": "John Doe",
        "date": "2025-04-14",
        "category": "Tech",
        "tags": ["flask", "api"],
        "comments": []
    },
    {
        "id": 2,
        "title": "Second post",
        "content": "This is the second post.",
        "author": "Jane Doe",
        "date": "2025-04-14",
        "category": "Lifestyle",
        "tags": ["health", "fitness"],
        "comments": []
    },
]


def validate_post_data(data):
    missing_fields = []
    if 'title' not in data or not data['title']:
        missing_fields.append('title')
    if 'content' not in data or not data['content']:
        missing_fields.append('content')
    return missing_fields


def find_post_by_id(post_id, posts):
    post = next((post for post in posts if str(post['id']) == str(post_id)), {})
    return post


def generate_new_id(data) -> int:
    new_id = max(post['id'] for post in data) + 1
    return new_id


def search_posts_by_fields(title_term, content_term, author_term, date_term, category_term, tag_term, posts):
    result = []
    seen_ids = set()

    for post in posts:
        match = False

        if title_term.strip() and title_term.lower() in post.get("title", "").lower():
            match = True
        if content_term.strip() and content_term.lower() in post.get("content", "").lower():
            match = True
        if author_term.strip() and author_term.lower() in post.get("author", "").lower():
            match = True
        if date_term.strip() and date_term in post.get("date", ""):
            match = True
        if category_term.strip() and category_term.lower() in post.get("category", "").lower():
            match = True
        if tag_term.strip() and tag_term.lower() in [t.lower() for t in post.get("tags", [])]:
            match = True

        if match and post["id"] not in seen_ids:
            result.append(post)
            seen_ids.add(post["id"])

    return result


def sort_posts(posts, field, order="asc"):
    order_parameter = (order == "desc")

    def sort_key(post):
        if field == "date":
            try:
                return datetime.strptime(post.get("date", ""), "%Y-%m-%d")
            except ValueError:
                return datetime.min
        if field == "comments":
            return len(post.get("comments", []))
        if field == "tags":
            tag_terms = [t.strip().lower() for t in request.args.get("tag", "").split(",") if t.strip()]
            post_tags = [t.lower() for t in post.get("tags", [])]
            return sum(1 for tag in tag_terms if tag in post_tags)
        return post.get(field, "")

    sorted_posts = sorted(posts, key=sort_key, reverse=order_parameter)
    return sorted_posts


def paginate_items(items):
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "page and limit must be integers."}), 400, True

    if page < 1 or limit < 1:
        return jsonify({"error": "page and limit must be greater than 0."}), 400, True

    start = (page - 1) * limit
    end = start + limit
    return items[start:end], None, False


@app.route("/api/v1/register", methods=["POST"])
@limiter.limit("10 per hour")
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if any(user["username"] == username for user in USERS):
        return jsonify({"error": "Username already exists"}), 400

    hashed_password = pbkdf2_sha256.hash(password)
    USERS.append({"username": username, "password": hashed_password})
    return jsonify({"message": f"User {username} registered successfully"}), 201


@app.route("/api/v1/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = next((user for user in USERS if user["username"] == username), None)
    if not user or not pbkdf2_sha256.verify(password, user["password"]):
        return jsonify({"error": "Invalid username or password"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200


@app.route('/api/v1/posts', methods=['GET', 'POST'])
def handle_posts():
    if request.method == 'POST':
        @jwt_required()
        def protected_create_post():
            new_post = request.get_json()

            missing_data = validate_post_data(new_post)
            if missing_data:
                return jsonify({"error": f"Invalid data. Data requires {missing_data}"}), 400

            if 'date' not in new_post or not new_post['date']:
                new_post["date"] = datetime.now().strftime("%Y-%m-%d")
            new_post.setdefault("category", "")
            new_post.setdefault("tags", [])
            new_post.setdefault("comments", [])

            new_post["id"] = generate_new_id(POSTS)
            new_post["author"] = get_jwt_identity()

            POSTS.append(new_post)
            return jsonify(new_post), 201

        return protected_create_post()

    paginated_items, error_response, is_error = paginate_items(POSTS)
    if is_error:
        return error_response

    required_fields = ["id", "title", "content", "author", "date", "category", "comments", "tags"]
    field_to_sort = request.args.get("sort", "").lower()
    if field_to_sort and not field_to_sort in required_fields:
        return jsonify({"error": f"'{field_to_sort}' is not a valid field to sort. Try: {required_fields}"}), 400

    required_direction = ["asc", "desc"]
    sort_direction = request.args.get("direction", "").lower()
    if sort_direction and not sort_direction in required_direction:
        return jsonify(
            {"error": f"'{sort_direction}' is not a valid direction to sort. Try: {required_direction}"}), 400

    if not field_to_sort and sort_direction:
        return jsonify({"error": f"'sort'-parameter is required. Try: {required_fields}"}), 400

    if field_to_sort:
        sorted_posts = sort_posts(POSTS, field_to_sort, sort_direction)
    else:
        sorted_posts = POSTS

    paginated_items, error_response, is_error = paginate_items(sorted_posts)
    if is_error:
        return error_response
    return jsonify(paginated_items)


@app.route('/api/v1/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    post = find_post_by_id(post_id, POSTS)

    if not post:
        return jsonify({"error": f"Post with id {post_id} not found."}), 404

    current_user = get_jwt_identity()
    if post.get("author") != current_user:
        return jsonify({"error": "You are not authorized to delete this post."}), 403

    POSTS.remove(post)
    return jsonify({"message": f"Post with id {post_id} has been deleted successfully."}), 200


@app.route('/api/v1/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    new_post_data = request.get_json()
    missing_data = validate_post_data(new_post_data)
    if missing_data:
        return jsonify({"error": f"Invalid data. Data requires {missing_data}"}), 400

    post = find_post_by_id(post_id, POSTS)
    if not post:
        return jsonify({"error": f"Post with id {post_id} not found."}), 404

    current_user = get_jwt_identity()
    if post.get("author") != current_user:
        return jsonify({"error": "You are not authorized to update this post."}), 403

    # Remove 'author' if someone tries to override it
    if "author" in new_post_data:
        del new_post_data["author"]

    # Validate 'date' format if provided
    if "date" in new_post_data:
        try:
            datetime.strptime(new_post_data["date"], "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Date must be in format YYYY-MM-DD"}), 400

    post.update(new_post_data)
    return jsonify(post), 200


@app.route('/api/v1/posts/search')
def search_post():
    title_term = request.args.get('title', '')
    content_term = request.args.get('content', '')
    author_term = request.args.get('author', '')
    date_term = request.args.get('date', '')
    category_term = request.args.get('category', '')
    tag_term = request.args.get('tag', '')

    results = search_posts_by_fields(title_term, content_term, author_term, date_term, category_term, tag_term, POSTS)

    paginated_items, error_response, is_error = paginate_items(results)
    if is_error:
        return error_response
    return jsonify(paginated_items)


@app.route('/api/v1/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    post = find_post_by_id(post_id, POSTS)
    if not post:
        return jsonify({"error": f"Post with id {post_id} not found."}), 404

    new_comment = request.get_json()
    if "author" not in new_comment or "text" not in new_comment:
        return jsonify({"error": "Comment must include 'author' and 'text'"}), 400

    new_comment["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    post.setdefault("comments", []).append(new_comment)
    return jsonify(post), 201


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
