import React from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
} from '@mui/material';
import {
  School as SchoolIcon,
  Assignment as AssignmentIcon,
  Grade as GradeIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { useAuth } from '../../context/AuthContext';
import { coursesAPI, analyticsAPI } from '../../api/axios';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const { user, hasRole } = useAuth();
  const navigate = useNavigate();

  const { data: courses, isLoading: coursesLoading } = useQuery(
    ['courses', 'dashboard'],
    () => coursesAPI.getAll({ limit: 5 })
  );

  const { data: analytics, isLoading: analyticsLoading } = useQuery(
    ['analytics', user?.id],
    () => analyticsAPI.getStudentAnalytics(user?.id),
    { enabled: hasRole('student') }
  );

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Доброе утро';
    if (hour < 18) return 'Добрый день';
    return 'Добрый вечер';
  };

  const renderStudentDashboard = () => (
    <Grid container spacing={3}>
      {/* Welcome Card */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3, bgcolor: 'primary.main', color: 'white' }}>
          <Typography variant="h5">
            {getGreeting()}, {user?.first_name}!
          </Typography>
          <Typography variant="body1" sx={{ mt: 1, opacity: 0.9 }}>
            Продолжайте в том же духе. У вас {analytics?.in_progress_courses || 0} активных курсов
          </Typography>
        </Paper>
      </Grid>

      {/* Stats Cards */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <SchoolIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Текущие курсы</Typography>
            </Box>
            <Typography variant="h3">{analytics?.in_progress_courses || 0}</Typography>
            <Typography variant="body2" color="text.secondary">
              Завершено: {analytics?.completed_courses || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <GradeIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Средний балл</Typography>
            </Box>
            <Typography variant="h3">{analytics?.overall_gpa?.toFixed(2) || '0.00'}</Typography>
            <Typography variant="body2" color="text.secondary">
              Из 5.0
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TrendingUpIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Рейтинг в группе</Typography>
            </Box>
            <Typography variant="h3">#{analytics?.group_rank || 'N/A'}</Typography>
            <Typography variant="body2" color="text.secondary">
              Из {analytics?.group_size || 'N/A'} студентов
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Recent Courses */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Недавние курсы
          </Typography>
          <List>
            {courses?.data?.map((course) => (
              <ListItem
                key={course.id}
                button
                onClick={() => navigate(`/courses/${course.id}`)}
              >
                <ListItemIcon>
                  <SchoolIcon />
                </ListItemIcon>
                <ListItemText
                  primary={course.name_ru}
                  secondary={`Преподаватель: ${course.teacher_name}`}
                />
                <Chip
                  label={`Прогресс: ${course.progress || 0}%`}
                  size="small"
                  color="primary"
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Grid>

      {/* Upcoming Deadlines */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Ближайшие дедлайны
          </Typography>
          <List>
            {analytics?.upcoming_deadlines?.map((deadline) => (
              <ListItem key={deadline.id}>
                <ListItemText
                  primary={deadline.title}
                  secondary={`До сдачи: ${deadline.days_remaining} дней`}
                />
                <Chip
                  label={deadline.days_remaining < 3 ? 'Срочно' : 'В процессе'}
                  color={deadline.days_remaining < 3 ? 'error' : 'default'}
                  size="small"
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Grid>

      {/* At Risk Courses */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Требуют внимания
          </Typography>
          {analytics?.at_risk_courses?.length > 0 ? (
            <List>
              {analytics.at_risk_courses.map((course) => (
                <ListItem key={course.id}>
                  <ListItemIcon>
                    <WarningIcon color="warning" />
                  </ListItemIcon>
                  <ListItemText
                    primary={course.name}
                    secondary={`Текущий балл: ${course.current_grade}`}
                  />
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => navigate(`/courses/${course.id}`)}
                  >
                    Перейти
                  </Button>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography color="text.secondary">
              Отлично! Все курсы в порядке
            </Typography>
          )}
        </Paper>
      </Grid>
    </Grid>
  );

  const renderTeacherDashboard = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Paper sx={{ p: 3, bgcolor: 'primary.main', color: 'white' }}>
          <Typography variant="h5">
            {getGreeting()}, {user?.first_name}!
          </Typography>
          <Typography variant="body1" sx={{ mt: 1, opacity: 0.9 }}>
            У вас {courses?.data?.length || 0} активных курсов и {analytics?.pending_reviews || 0} работ на проверке
          </Typography>
        </Paper>
      </Grid>

      {/* Stats Cards */}
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">Активные курсы</Typography>
            <Typography variant="h3">{courses?.data?.length || 0}</Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">Всего студентов</Typography>
            <Typography variant="h3">{analytics?.total_students || 0}</Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">На проверке</Typography>
            <Typography variant="h3">{analytics?.pending_reviews || 0}</Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">Средняя оценка</Typography>
            <Typography variant="h3">{analytics?.average_grade?.toFixed(2) || '0.00'}</Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* My Courses */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Мои курсы</Typography>
            <Button
              variant="contained"
              startIcon={<SchoolIcon />}
              onClick={() => navigate('/courses/new')}
            >
              Создать курс
            </Button>
          </Box>
          <List>
            {courses?.data?.map((course) => (
              <ListItem
                key={course.id}
                button
                onClick={() => navigate(`/courses/${course.id}`)}
              >
                <ListItemText
                  primary={course.name_ru}
                  secondary={`${course.student_count || 0} студентов • ${course.assignment_count || 0} заданий`}
                />
                <Chip
                  label={`${course.pending_grades || 0} на проверке`}
                  color={course.pending_grades > 0 ? 'warning' : 'default'}
                  size="small"
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Grid>

      {/* Pending Reviews */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Ожидают проверки
          </Typography>
          {analytics?.pending_submissions?.length > 0 ? (
            <List>
              {analytics.pending_submissions.map((submission) => (
                <ListItem key={submission.id}>
                  <ListItemText
                    primary={submission.student_name}
                    secondary={`${submission.assignment_title} • ${new Date(submission.submitted_at).toLocaleDateString()}`}
                  />
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => navigate(`/submissions/${submission.id}`)}
                  >
                    Проверить
                  </Button>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography color="text.secondary">
              Нет работ на проверке
            </Typography>
          )}
        </Paper>
      </Grid>
    </Grid>
  );

  if (coursesLoading || analyticsLoading) {
    return <LinearProgress />;
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {hasRole('student') && renderStudentDashboard()}
      {hasRole('teacher') && renderTeacherDashboard()}
      {hasRole('admin') && (
        <Typography variant="h4">Панель администратора</Typography>
      )}
    </Box>
  );
};

export default Dashboard;