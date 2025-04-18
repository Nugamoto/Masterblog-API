import json
import os
from datetime import datetime
from typing import List, Dict, Tuple, Union

from flask import jsonify, request

POSTS_FILE = os.path.join(os.path.dirname(__file__), "posts.json")
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def load_json(filepath: str) -> List[Dict]:
    """Load JSON data from the specified file."""
    try:
        with open(filepath, "r", encoding="utf-8") as fileobject:
            return json.load(fileobject)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_json(content: List[Dict], filepath: str) -> None:
    """Save content as JSON data into the specified file atomically."""
    if not isinstance(content, list):
        raise TypeError("Provided content must be a list")

    temp_filepath = filepath + ".tmp"

    try:
        with open(temp_filepath, "w", encoding="utf-8") as temp_file:
            json.dump(content, temp_file, indent=4)
        os.replace(temp_filepath, filepath)
    except (IOError, OSError) as e:
        raise IOError(f"Failed to write to file {filepath}") from e
    except TypeError as e:
        raise TypeError("Provided content could not be serialized to JSON") from e


def validate_post_data(data: Dict) -> List[str]:
    """Validate that the essential fields of a blog post are present."""
    missing_fields = []
    if 'title' not in data or not data['title']:
        missing_fields.append('title')
    if 'content' not in data or not data['content']:
        missing_fields.append('content')
    return missing_fields


def find_post_by_id(post_id: Union[int, str], posts: List[Dict]) -> Dict:
    """Find and return a post by its ID from a list of posts."""
    return next((post for post in posts if str(post.get('id')) == str(post_id)), {})


def generate_new_id(data: List[Dict]) -> int:
    """Generate a new unique ID for a blog post."""
    if not data:
        return 1
    return max((post.get("id", 0) for post in data), default=0) + 1


def search_posts_by_fields(
    title_term: str,
    content_term: str,
    author_term: str,
    date_term: str,
    category_term: str,
    tag_term: str,
    posts: List[Dict]
) -> List[Dict]:
    """Search for blog posts matching any of the provided search criteria."""
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

        if match and post.get("id") not in seen_ids:
            result.append(post)
            seen_ids.add(post.get("id"))

    return result


def sort_posts(posts: List[Dict], field: str, order: str = "asc") -> List[Dict]:
    """Sort a list of posts based on a specified field."""
    order_parameter = (order == "desc")

    def sort_key(post: Dict):
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

    return sorted(posts, key=sort_key, reverse=order_parameter)


def paginate_items(items: List[Dict]) -> Tuple[List[Dict], Union[Dict, None], bool]:
    """Paginate a list of items based on query parameters 'page' and 'limit'."""
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return [], jsonify({"error": "page and limit must be integers."}), True

    if page < 1 or limit < 1:
        return [], jsonify({"error": "page and limit must be greater than 0."}), True

    start = (page - 1) * limit
    end = start + limit
    return items[start:end], None, False