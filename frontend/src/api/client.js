const API_BASE = '/api';

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('token');
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  async request(path, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.setToken(null);
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    if (response.status === 204) {
      return null;
    }

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Something went wrong');
    }

    return data;
  }

  // Auth
  async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.access_token);
    return data;
  }

  logout() {
    this.setToken(null);
  }

  // Projects
  async getProjects() {
    return this.request('/projects');
  }

  async createProject(name, description) {
    return this.request('/projects', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
  }

  async getProject(projectId) {
    return this.request(`/projects/${projectId}`);
  }

  async getProjectMembers(projectId) {
    return this.request(`/projects/${projectId}/members`);
  }

  async addProjectMember(projectId, email) {
    return this.request(`/projects/${projectId}/members`, {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  // Tasks
  async getTasks(projectId, status = null, limit = 50, offset = 0) {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    params.set('limit', limit);
    params.set('offset', offset);
    return this.request(`/projects/${projectId}/tasks?${params.toString()}`);
  }

  async createTask(projectId, task) {
    return this.request(`/projects/${projectId}/tasks`, {
      method: 'POST',
      body: JSON.stringify(task),
    });
  }

  async updateTask(projectId, taskId, updates) {
    return this.request(`/projects/${projectId}/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteTask(projectId, taskId) {
    return this.request(`/projects/${projectId}/tasks/${taskId}`, {
      method: 'DELETE',
    });
  }

  // Comments
  async getComments(projectId, taskId) {
    return this.request(`/projects/${projectId}/tasks/${taskId}/comments`);
  }

  async createComment(projectId, taskId, content) {
    return this.request(`/projects/${projectId}/tasks/${taskId}/comments`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  async deleteComment(projectId, taskId, commentId) {
    return this.request(`/projects/${projectId}/tasks/${taskId}/comments/${commentId}`, {
      method: 'DELETE',
    });
  }

  // Activity
  async getActivity(projectId, limit = 30) {
    return this.request(`/projects/${projectId}/activity?limit=${limit}`);
  }
}

export const api = new ApiClient();