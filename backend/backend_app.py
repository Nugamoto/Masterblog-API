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


def generate_new_id(data) -> int:
    new_id = max(post['id'] for post in data) + 1
    return new_id


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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
