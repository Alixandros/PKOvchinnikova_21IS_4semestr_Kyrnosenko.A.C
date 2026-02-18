const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// Аутентификация
async function register(userData) {
  const response = await api.post('/register', userData);
  return response.data;
}

async function login(email, password) {
  const formData = new FormData();
  formData.append('username', email);
  formData.append('password', password);
  const response = await api.post('/token', formData);
  return response.data;
}

// Курсы
async function getCourses() {
  const response = await api.get('/courses');
  return response.data;
}

async function createCourse(courseData) {
  const response = await api.post('/courses', courseData);
  return response.data;
}

async function enrollInCourse(courseId) {
  const response = await api.post(`/courses/${courseId}/enroll`);
  return response.data;
}

// Задания
async function getAssignments(courseId) {
  const response = await api.get(`/courses/${courseId}/assignments`);
  return response.data;
}

async function createAssignment(courseId, assignmentData) {
  const response = await api.post(`/courses/${courseId}/assignments`, assignmentData);
  return response.data;
}

// Работы
async function submitWork(assignmentId, filePath, comment) {
  const response = await api.post(`/assignments/${assignmentId}/submit`, {
    file_path: filePath,
    comment: comment
  });
  return response.data;
}

async function getSubmissions(assignmentId) {
  const response = await api.get(`/assignments/${assignmentId}/submissions`);
  return response.data;
}

async function gradeSubmission(submissionId, grade, feedback) {
  const response = await api.post(`/submissions/${submissionId}/grade`, {
    grade: grade,
    feedback: feedback
  });
  return response.data;
}

// Оценки
async function getMyGrades() {
  const response = await api.get('/my-grades');
  return response.data;
}