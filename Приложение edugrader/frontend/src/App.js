import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from 'react-query';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ru } from 'date-fns/locale';

import { AuthProvider } from './context/AuthContext';
import PrivateRoute from './components/Auth/PrivateRoute';
import Layout from './components/Layout/Layout';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import Dashboard from './components/Dashboard/Dashboard';
import CourseList from './components/Courses/CourseList';
import CourseDetail from './components/Courses/CourseDetail';
import AssignmentList from './components/Assignments/AssignmentList';
import AssignmentDetail from './components/Assignments/AssignmentDetail';
import SubmissionList from './components/Submissions/SubmissionList';
import SubmissionForm from './components/Submissions/SubmissionForm';
import GradeView from './components/Grades/GradeView';
import Analytics from './components/Analytics/Analytics';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ru}>
          <CssBaseline />
          <AuthProvider>
            <Router>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                
                <Route path="/" element={
                  <PrivateRoute>
                    <Layout />
                  </PrivateRoute>
                }>
                  <Route index element={<Navigate to="/dashboard" replace />} />
                  <Route path="dashboard" element={<Dashboard />} />
                  
                  <Route path="courses">
                    <Route index element={<CourseList />} />
                    <Route path=":courseId" element={<CourseDetail />} />
                    <Route path=":courseId/assignments" element={<AssignmentList />} />
                    <Route path=":courseId/assignments/:assignmentId" element={<AssignmentDetail />} />
                  </Route>
                  
                  <Route path="submissions">
                    <Route path="assignment/:assignmentId" element={<SubmissionList />} />
                    <Route path="new/:assignmentId" element={<SubmissionForm />} />
                  </Route>
                  
                  <Route path="grades">
                    <Route path=":gradeId" element={<GradeView />} />
                  </Route>
                  
                  <Route path="analytics">
                    <Route path="course/:courseId" element={<Analytics />} />
                  </Route>
                </Route>
              </Routes>
            </Router>
          </AuthProvider>
        </LocalizationProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;