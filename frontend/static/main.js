// ==================== GLOBAL ====================
window.onload = () => {
  const savedBaseUrl = localStorage.getItem("apiBaseUrl");
  if (savedBaseUrl) {
    document.getElementById("api-base-url").value = savedBaseUrl;
    loadPosts();
    showLoggedInUserFromToken();
  }
};

// ==================== AUTH ====================
function registerUser() {
  const baseUrl = getBaseUrl();
  const username = getValue("register-username");
  const password = getValue("register-password");

  fetch(`${baseUrl}/register`, requestOptions("POST", { username, password }))
    .then(toJSON)
    .then(() => {
      alert("User registered successfully.");
      resetFields("register-username", "register-password");
    })
    .catch(logError);
}

function loginUser() {
  const baseUrl = getBaseUrl();
  const username = getValue("login-username");
  const password = getValue("login-password");

  fetch(`${baseUrl}/login`, requestOptions("POST", { username, password }))
    .then(toJSON)
    .then((data) => {
      if (data.access_token) {
        localStorage.setItem("jwt_token", data.access_token);
        alert("Login successful!");
        updateLoggedInUserDisplay(username);
        resetFields("login-username", "login-password");
      } else {
        alert("Login failed: " + JSON.stringify(data));
      }
    })
    .catch(logError);
}

function logoutUser() {
  localStorage.removeItem("jwt_token");
  setText("logged-in-user", "");
  loadPosts();
}

function showLoggedInUserFromToken() {
  const token = localStorage.getItem("jwt_token");
  if (!token) return;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    updateLoggedInUserDisplay(payload.sub || "Unknown");
  } catch (e) {
    console.warn("Invalid token format", e);
  }
}

function updateLoggedInUserDisplay(username) {
  setText("logged-in-user", `Logged in as: ${username}`);
}

// ==================== POSTS ====================
function loadPosts() {
  const baseUrl = getBaseUrl();
  localStorage.setItem("apiBaseUrl", baseUrl);

  let url = `${baseUrl}/posts`;
  const params = new URLSearchParams();

  // always append page & limit
  addIfExists(params, "page", "page-number");
  addIfExists(params, "limit", "limit-number");

  // ONLY append sort & direction if sort is non-empty
  const sort = document.getElementById("sort-field").value;
  if (sort !== "") {
    params.append("sort", sort);
    const direction = document.getElementById("sort-direction").value;
    if (direction !== "") {
      params.append("direction", direction);
    }
  }

  const queryString = params.toString();
  if (queryString) {
    url += `?${queryString}`;
  }

  console.log("Fetching posts from:", url);
  fetch(url)
    .then(toJSON)
    .then(renderPosts)
    .catch(logError);
}

function addPost() {
  const baseUrl = getBaseUrl();
  const post = {
    title: getValue("post-title"),
    content: getValue("post-content"),
    category: getValue("post-category"),
    tags: getValue("post-tags")
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean),
  };

  fetch(`${baseUrl}/posts`, requestOptions("POST", post, true))
    .then(toJSON)
    .then(() => loadPosts())
    .catch(logError);
}

function deletePost(postId) {
  const baseUrl = getBaseUrl();
  fetch(`${baseUrl}/posts/${postId}`, requestOptions("DELETE", null, true))
    .then(toJSON)
    .then(() => loadPosts())
    .catch(logError);
}

function editPost(postId) {
  const baseUrl = getBaseUrl();
  const updated = {
    title: prompt("Enter new title:"),
    content: prompt("Enter new content:"),
    category: prompt("Enter new category:"),
    tags: prompt("Enter new tags (comma separated):")
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean),
  };

  fetch(`${baseUrl}/posts/${postId}`, requestOptions("PUT", updated, true))
    .then(toJSON)
    .then(() => loadPosts())
    .catch(logError);
}

function searchPosts() {
  const baseUrl = getBaseUrl();
  const params = new URLSearchParams();

  ["title", "author", "category", "tag"].forEach((field) => {
    const value = getValue(`search-${field}`);
    if (value) params.append(field, value);
  });

  fetch(`${baseUrl}/posts/search?${params.toString()}`)
    .then(toJSON)
    .then(renderPosts)
    .catch(logError);
}

function promptAddComment(postId) {
  const comment = prompt("Enter your comment:");
  if (comment) addComment(postId, comment);
}

function addComment(postId, text) {
  const baseUrl = getBaseUrl();
  fetch(`${baseUrl}/posts/${postId}/comments`, requestOptions("POST", { text }, true))
    .then(toJSON)
    .then(() => loadPosts())
    .catch(logError);
}

// ==================== RENDER ====================
function renderPosts(posts) {
  const container = document.getElementById("post-container");
  container.innerHTML = "";

  posts.forEach(({ id, title, author, date, content, category, tags, comments }) => {
    const post = document.createElement("div");
    post.className = "post";
    post.innerHTML = `
      <h2>${title}</h2>
      <p class="post-meta">By <span>${author}</span> on <span>${date}</span></p>
      <p>${content}</p>
      <p><strong>Category:</strong> ${category} | <strong>Tags:</strong> ${tags.join(", ")}</p>
      <div class="button-group">
        <button class="button-delete" onclick="deletePost(${id})">Delete</button>
        <button class="button-edit" onclick="editPost(${id})">Edit</button>
        <button class="button-comment" onclick="promptAddComment(${id})">Add Comment</button>
      </div>
      <div class="comments">
        ${comments?.length
          ? comments.map((c) => `<p><strong>${c.author}:</strong> ${c.text} (${c.timestamp})</p>`).join("")
          : "<p>No comments yet.</p>"}
      </div>
    `;
    container.appendChild(post);
  });
}

// ==================== HELPERS ====================
function getValue(id) {
  return document.getElementById(id)?.value || "";
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.innerText = text;
}

function resetFields(...ids) {
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
}

function getBaseUrl() {
  return getValue("api-base-url");
}

function requestOptions(method, data = null, withAuth = false) {
  const headers = { "Content-Type": "application/json" };
  if (withAuth) headers["Authorization"] = `Bearer ${localStorage.getItem("jwt_token")}`;

  const options = { method, headers };
  if (data) options.body = JSON.stringify(data);
  return options;
}

function toJSON(response) {
  return response.json();
}

function logError(error) {
  console.error("Error:", error);
}

function addIfExists(params, paramName, elementId) {
  const value = getValue(elementId);
  if (value) params.append(paramName, value);
}

function toggleDarkMode() {
  document.body.classList.toggle("dark-mode");
}

function scrollToAddPost() {
  const input = document.getElementById("post-title");
  if (input) {
    input.scrollIntoView({ behavior: "smooth", block: "start" });
    input.focus();
  }
}