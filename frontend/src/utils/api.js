import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Auth API calls
export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

// Blog API calls
export const blogAPI = {
  getAllBlogs: () => api.get('/blogs'),
  getMyBlogs: () => api.get('/blogs/my'),
  getBlog: (id) => api.get(`/blogs/${id}`),
  createBlog: (data) => api.post('/blogs', data),
  deleteBlog: (id) => api.delete(`/blogs/${id}`),
  getEntityDetails: (blogId) => api.get(`/blogs/${blogId}/entities`),
  saveEntityDetails: (blogId, formData) => {
    // Use axios directly for multipart/form-data
    const token = localStorage.getItem('token');
    return axios.post(`${API_URL}/blogs/${blogId}/entity-details`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': token ? `Bearer ${token}` : ''
      }
    });
  }
};

// User API calls
export const userAPI = {
  getProfile: () => api.get('/users/profile'),
};

export default api;
