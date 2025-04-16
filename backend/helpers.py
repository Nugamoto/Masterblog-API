import json
import os
from datetime import datetime

from flask import jsonify, request

POSTS_FILE = os.path.join(os.path.dirname(__file__), "posts.json")


def load_json(filepath=POSTS_FILE):
    """Load JSON data from the specified file.

    This function attempts to open and parse the JSON file located at the given
    filepath. If the file does not exist or contains invalid JSON, an empty list is returned.

    Args:
        filepath (str): The path to the JSON file. Defaults to POSTS_FILE.

    Returns:
        list: A list containing the JSON data, or an empty list if an error occurs.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as fileobject:
            return json.load(fileobject)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_json(content, filepath=POSTS_FILE):
    """Save content as JSON data into the specified file atomically.

    The function first writes the data to a temporary file and then atomically
    replaces the original file with it. This prevents file corruption during
    unexpected interruptions.

    Args:
        content (list): The content to be saved. Must be a list.
        filepath (str): The path to the JSON file. Defaults to POSTS_FILE.

    Raises:
        TypeError: If the provided content is not a list or cannot be serialized to JSON.
        IOError: If writing to the file fails.
    """
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


def validate_post_data(data):
    """Validate that the essential fields of a blog post are present.

    This function checks whether the provided data dictionary contains
    non-empty 'title' and 'content' fields.

    Args:
        data (dict): The blog post data to validate.

    Returns:
        list: A list of missing field names. An empty list indicates that all required fields are present.
    """
    missing_fields = []
    if 'title' not in data or not data['title']:
        missing_fields.append('title')
    if 'content' not in data or not data['content']:
        missing_fields.append('content')
    return missing_fields


def find_post_by_id(post_id, posts):
    """Find and return a post by its ID from a list of posts.

    The function searches for a post whose 'id' matches the provided post_id.

    Args:
        post_id (int or str): The identifier of the post.
        posts (list): A list of post dictionaries.

    Returns:
        dict: The post matching the given ID. If no matching post is found, returns an empty dictionary.
    """
    post = next((post for post in posts if str(post['id']) == str(post_id)), {})
    return post


def generate_new_id(data) -> int:
    """Generate a new unique ID for a blog post.

    The new ID is determined by taking the maximum current ID in the data and adding 1.
    If the data list is empty, returns 1.

    Args:
        data (list): A list of post dictionaries.

    Returns:
        int: The new post ID.
    """
    if not data:
        return 1
    return max(post['id'] for post in data) + 1


def search_posts_by_fields(title_term, content_term, author_term, date_term, category_term, tag_term, posts):
    """Search for blog posts matching any of the provided search criteria.

    This function checks each post to see if any of the search terms (for title, content,
    author, date, category, and tags) are present. A post is included in the result if at least one field matches.
    Duplicate posts are avoided using an internal seen_ids set.

    Args:
        title_term (str): Search term for the title.
        content_term (str): Search term for the content.
        author_term (str): Search term for the author.
        date_term (str): Search term for the date.
        category_term (str): Search term for the category.
        tag_term (str): Search term for the tags.
        posts (list): The list of posts to search within.

    Returns:
        list: A list of posts that match any of the search criteria.
    """
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
    """Sort a list of posts based on a specified field.

    The sorting behavior differs based on the field:
    - For 'date', string dates are converted to datetime objects.
    - For 'comments', sorting is based on the number of comments.
    - For 'tags', sorting is based on the count of matching tags from the query parameter.
    - For other fields, the post's field value is used directly.

    Args:
        posts (list): The list of posts to sort.
        field (str): The field by which to sort.
        order (str, optional): 'asc' for ascending or 'desc' for descending sort order. Defaults to "asc".

    Returns:
        list: The sorted list of posts.
    """
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
    """Paginate a list of items based on query parameters 'page' and 'limit'.

    The function reads the 'page' and 'limit' parameters from the request's query string,
    calculates the appropriate slice of the items list, and returns the paginated items.
    In case of an invalid parameter, an error response is returned.

    Args:
        items (list): The list of items to paginate.

    Returns:
        tuple: A tuple containing:
            - The paginated list of items (if successful),
            - An error response (if an error occurred, otherwise None),
            - A boolean flag indicating whether an error occurred.
    """
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