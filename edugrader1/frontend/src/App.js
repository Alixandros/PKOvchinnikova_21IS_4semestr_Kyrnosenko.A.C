import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import {
  AppBar, Toolbar, Typography, Button, Container, Paper,
  TextField, Box, Card, CardContent, Grid, List, ListItem,
  ListItemText, Drawer, IconButton, Avatar, Menu, MenuItem,
  Alert, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  LinearProgress
} from '@mui/material';
import {
  Menu as MenuIcon,
  School, Assignment, Grade, ExitToApp,
  CloudUpload, InsertDriveFile
} from '@mui/icons-material';
import api from './api';

// Login Component
const Login = ({ onLogin }) => {
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const formData = new FormData();
      formData.append('username', form.username);
      formData.append('password', form.password);
      
      const res = await api.post('/auth/login', formData);
      localStorage.setItem('token', res.data.access_token);
      onLogin();
    } catch (err) {
      setError('Invalid username or password');
    }
  };

  return (
    <Container maxWidth="sm">
      <Paper sx={{ p: 4, mt: 8 }}>
        <Typography variant="h4" align="center" gutterBottom>
          EduGrader
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth margin="normal" label="Username"
            value={form.username} onChange={(e) => setForm({...form, username: e.target.value})}
          />
          <TextField
            fullWidth margin="normal" label="Password" type="password"
            value={form.password} onChange={(e) => setForm({...form, password: e.target.value})}
          />
          <Button fullWidth variant="contained" type="submit" sx={{ mt: 2 }}>
            Login
          </Button>
        </form>
      </Paper>
    </Container>
  );
};

// Dashboard Component
const Dashboard = ({ user }) => {
  const [courses, setCourses] = useState([]);
  const [assignments, setAssignments] = useState([]);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    const res = await api.get('/courses');
    setCourses(res.data);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome, {user?.full_name}!
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Your Courses</Typography>
              <List>
                {courses.map(course => (
                  <ListItem key={course.id}>
                    <ListItemText 
                      primary={course.name} 
                      secondary={`${course.code} - ${course.students_count} students`}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Recent Activity</Typography>
              <Typography color="textSecondary">No recent activity</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

// Courses Component
const CoursesPage = ({ user }) => {
  const [courses, setCourses] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [newCourse, setNewCourse] = useState({ name: '', code: '', description: '' });

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    const res = await api.get('/courses');
    setCourses(res.data);
  };

  const createCourse = async () => {
    await api.post('/courses', newCourse);
    setOpenDialog(false);
    fetchCourses();
  };

  const enrollCourse = async (courseId) => {
    await api.post(`/courses/${courseId}/enroll`);
    fetchCourses();
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" mb={2}>
        <Typography variant="h4">Courses</Typography>
        {user?.role === 'teacher' && (
          <Button variant="contained" onClick={() => setOpenDialog(true)}>
            Create Course
          </Button>
        )}
      </Box>

      <Grid container spacing={2}>
        {courses.map(course => (
          <Grid item xs={12} md={6} lg={4} key={course.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{course.name}</Typography>
                <Typography color="textSecondary">{course.code}</Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {course.description}
                </Typography>
                <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
                  <Chip label={`${course.students_count} students`} size="small" />
                  {user?.role === 'student' && (
                    <Button size="small" onClick={() => enrollCourse(course.id)}>
                      Enroll
                    </Button>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Create Course</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus margin="dense" label="Course Name" fullWidth
            value={newCourse.name} onChange={(e) => setNewCourse({...newCourse, name: e.target.value})}
          />
          <TextField
            margin="dense" label="Course Code" fullWidth
            value={newCourse.code} onChange={(e) => setNewCourse({...newCourse, code: e.target.value})}
          />
          <TextField
            margin="dense" label="Description" fullWidth multiline rows={3}
            value={newCourse.description} onChange={(e) => setNewCourse({...newCourse, description: e.target.value})}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={createCourse} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

// Main App Component
function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const res = await api.get('/users/me');
      setUser(res.data);
    } catch (err) {
      localStorage.removeItem('token');
    }
    setLoading(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setAnchorEl(null);
  };

  if (loading) return <LinearProgress />;
  if (!user) return <Login onLogin={fetchUser} />;

  const menuItems = [
    { text: 'Dashboard', icon: <School />, path: '/' },
    { text: 'Courses', icon: <Assignment />, path: '/courses' },
  ];

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6">EduGrader</Typography>
      </Toolbar>
      {menuItems.map(item => (
        <Button
          key={item.text}
          fullWidth
          startIcon={item.icon}
          sx={{ justifyContent: 'flex-start', p: 2 }}
          onClick={() => window.location.href = item.path}
        >
          {item.text}
        </Button>
      ))}
    </Box>
  );

  return (
    <BrowserRouter>
      <Box sx={{ display: 'flex' }}>
        <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
          <Toolbar>
            <IconButton color="inherit" edge="start" onClick={() => setMobileOpen(!mobileOpen)} sx={{ mr: 2, display: { sm: 'none' } }}>
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>EduGrader</Typography>
            <IconButton color="inherit" onClick={(e) => setAnchorEl(e.currentTarget)}>
              <Avatar>{user.full_name[0]}</Avatar>
            </IconButton>
            <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
              <MenuItem onClick={handleLogout}>Logout</MenuItem>
            </Menu>
          </Toolbar>
        </AppBar>

        <Drawer variant="permanent" sx={{ display: { xs: 'none', sm: 'block' }, '& .MuiDrawer-paper': { width: 240 } }} open>
          {drawer}
        </Drawer>

        <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
          <Routes>
            <Route path="/" element={<Dashboard user={user} />} />
            <Route path="/courses" element={<CoursesPage user={user} />} />
          </Routes>
        </Box>
      </Box>
    </BrowserRouter>
  );
}

export default App;