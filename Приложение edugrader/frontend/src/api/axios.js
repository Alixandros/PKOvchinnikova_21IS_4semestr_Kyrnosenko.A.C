import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        // Refresh failed - redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// API endpoints
export const authAPI = {
  login: (data) => axiosInstance.post('/auth/login', data),
  register: (data) => axiosInstance.post('/auth/register', data),
  logout: () => axiosInstance.post('/auth/logout'),
  refreshToken: (data) => axiosInstance.post('/auth/refresh', data),
};

export const coursesAPI = {
  getAll: (params) => axiosInstance.get('/courses', { params }),
  getById: (id) => axiosInstance.get(`/courses/${id}`),
  create: (data) => axiosInstance.post('/courses', data),
  update: (id, data) => axiosInstance.put(`/courses/${id}`, data),
  delete: (id) => axiosInstance.delete(`/courses/${id}`),
  enrollStudent: (courseId, studentId) => 
    axiosInstance.post(`/courses/${courseId}/enroll/${studentId}`),
  batchEnroll: (courseId, emails) => 
    axiosInstance.post(`/courses/${courseId}/enroll/batch`, { student_emails: emails }),
};

export const assignmentsAPI = {
  getByCourse: (courseId) => axiosInstance.get(`/assignments/course/${courseId}`),
  getById: (id) => axiosInstance.get(`/assignments/${id}`),
  create: (data) => {
    const formData = new FormData();
    Object.keys(data).forEach(key => {
      if (key === 'files' && data[key]) {
        data[key].forEach(file => formData.append('files', file));
      } else {
        formData.append(key, data[key]);
      }
    });
    return axiosInstance.post('/assignments', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  publish: (id) => axiosInstance.put(`/assignments/${id}/publish`),
};

export const submissionsAPI = {
  submit: (data) => {
    const formData = new FormData();
    Object.keys(data).forEach(key => {
      formData.append(key, data[key]);
    });
    return axiosInstance.post('/submissions', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getByAssignment: (assignmentId) => 
    axiosInstance.get(`/submissions/assignment/${assignmentId}`),
  getById: (id) => axiosInstance.get(`/submissions/${id}`),
};

export const gradesAPI = {
  create: (data) => axiosInstance.post('/grades', data),
  update: (id, data) => axiosInstance.put(`/grades/${id}`, data),
  getStudentGrades: (studentId, courseId) => 
    axiosInstance.get(`/grades/student/${studentId}/course/${courseId}`),
  createAppeal: (gradeId, reason) => 
    axiosInstance.post(`/grades/${gradeId}/appeal`, { reason }),
};

export const analyticsAPI = {
  getStudentAnalytics: (studentId) => 
    axiosInstance.get(`/analytics/student/${studentId}`),
  getCourseAnalytics: (courseId) => 
    axiosInstance.get(`/analytics/course/${courseId}`),
  exportReport: (courseId, format = 'pdf') => 
    axiosInstance.get(`/analytics/course/${courseId}/export`, {
      params: { format },
      responseType: 'blob',
    }),
};

export default axiosInstance;