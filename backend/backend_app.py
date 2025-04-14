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


@app.route('/api/posts', methods=['GET', 'POST'])
def handle_posts():
    if request.method == 'POST':
        new_post = request.get_json()

        missing_data = validate_post_data(new_post)
        if missing_data:
            return jsonify({"error": f"Invalid data. Data requires {missing_data}"}), 400

        # Generate a new ID for the post
        new_post["id"] = generate_new_id(POSTS)

        # Add the new post to our list
        POSTS.append(new_post)

        # Return the new post data to the client
        return jsonify(new_post), 201

    return jsonify(POSTS)  # GET request


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
    return jsonify(results)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
