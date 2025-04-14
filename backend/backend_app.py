from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]


def validate_post_data(data) -> bool:
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


def search_posts_by_fields(title_term, content_term, posts):
    result = []
    seen_ids = set()

    if title_term.strip():
        title_term = title_term.lower()
        for post in posts:
            if title_term in post["title"].lower() and post["id"] not in seen_ids:
                result.append(post)
                seen_ids.add(post["id"])

    if content_term.strip():
        content_term = content_term.lower()
        for post in posts:
            if content_term in post["content"].lower() and post["id"] not in seen_ids:
                result.append(post)
                seen_ids.add(post["id"])

    return result


def sort_posts(posts, field, order="asc"):
    order_parameter = (order == "desc")
    sorted_posts = sorted(posts, key=lambda x: x.get(field, ""), reverse=order_parameter)
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


@app.route('/api/posts', methods=['GET', 'POST'])
def handle_posts():
    if request.method == 'POST':
        new_post = request.get_json()

        missing_data = validate_post_data(new_post)
        if missing_data:
            return jsonify({"error": f"Invalid data. Data requires {missing_data}"}), 400

        new_post["id"] = generate_new_id(POSTS)

        POSTS.append(new_post)

        return jsonify(new_post), 201

    paginated_items, error_response, is_error = paginate_items(POSTS)
    if is_error:
        return error_response

    required_fields = ["id", "title", "content"]
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


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    # Find the post with the given ID
    post = find_post_by_id(post_id, POSTS)

    # If the post wasn't found, return a 404 error
    if not post:
        return jsonify({"error": f"Post with id {post_id} not found."}), 404

    # Remove the post from the list
    POSTS.remove(post)

    # Return the deleted post
    return jsonify({"message": f"Post with id {post_id} has been deleted successfully."}), 200


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    new_post_data = request.get_json()
    missing_data = validate_post_data(new_post_data)
    if missing_data:
        return jsonify({"error": f"Invalid data. Data requires {missing_data}"}), 400

    post = find_post_by_id(post_id, POSTS)
    if not post:
        return jsonify({"error": f"Post with id {post_id} not found."}), 404

    post.update(new_post_data)

    return jsonify(post), 200


@app.route('/api/posts/search')
def search_post():
    title_term = request.args.get('title', '')
    content_term = request.args.get('content', '')

    results = search_posts_by_fields(title_term, content_term, POSTS)
    paginated_items, error_response, is_error = paginate_items(results)
    if is_error:
        return error_response
    return jsonify(paginated_items)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
