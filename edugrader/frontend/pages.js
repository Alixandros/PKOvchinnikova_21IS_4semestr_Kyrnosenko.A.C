const Pages = {
  Auth: ({ onLogin, onRegister, currentPage, setCurrentPage }) => {
    const [email, setEmail] = React.useState('');
    const [password, setPassword] = React.useState('');
    const [fullName, setFullName] = React.useState('');
    const [role, setRole] = React.useState('student');
    const [group, setGroup] = React.useState('');

    const handleSubmit = async (e) => {
      e.preventDefault();
      if (currentPage === 'login') {
        await onLogin(email, password);
      } else {
        await onRegister({ email, password, full_name: fullName, role, group });
      }
    };

    return React.createElement('div', { className: 'container' },
      React.createElement('h2', null, currentPage === 'login' ? 'Вход в EduGrader' : 'Регистрация'),
      React.createElement('div', { className: 'nav' },
        React.createElement('button', { 
          onClick: () => setCurrentPage('login'),
          style: { background: currentPage === 'login' ? '#1976d2' : '#ccc' }
        }, 'Вход'),
        React.createElement('button', { 
          onClick: () => setCurrentPage('register'),
          style: { background: currentPage === 'register' ? '#1976d2' : '#ccc' }
        }, 'Регистрация')
      ),
      React.createElement('form', { onSubmit: handleSubmit },
        React.createElement('input', {
          type: 'email',
          placeholder: 'Email',
          value: email,
          onChange: (e) => setEmail(e.target.value),
          required: true
        }),
        React.createElement('input', {
          type: 'password',
          placeholder: 'Пароль',
          value: password,
          onChange: (e) => setPassword(e.target.value),
          required: true
        }),
        currentPage === 'register' && [
          React.createElement('input', {
            key: 'name',
            placeholder: 'Полное имя',
            value: fullName,
            onChange: (e) => setFullName(e.target.value),
            required: true
          }),
          React.createElement('select', {
            key: 'role',
            value: role,
            onChange: (e) => setRole(e.target.value)
          },
            React.createElement('option', { value: 'student' }, 'Студент'),
            React.createElement('option', { value: 'teacher' }, 'Преподаватель')
          ),
          role === 'student' && React.createElement('input', {
            key: 'group',
            placeholder: 'Группа',
            value: group,
            onChange: (e) => setGroup(e.target.value)
          })
        ],
        React.createElement('button', { type: 'submit' },
          currentPage === 'login' ? 'Войти' : 'Зарегистрироваться'
        )
      )
    );
  },

  Dashboard: ({ user, logout, currentPage, setCurrentPage }) => {
    const [courses, setCourses] = React.useState([]);
    const [grades, setGrades] = React.useState([]);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
      loadData();
    }, []);

    async function loadData() {
      try {
        const coursesData = await getCourses();
        setCourses(coursesData);
        
        if (user?.role === 'student') {
          const gradesData = await getMyGrades();
          setGrades(gradesData);
        }
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setLoading(false);
      }
    }

    const renderContent = () => {
      switch(currentPage) {
        case 'dashboard':
          return React.createElement('div', null, [
            React.createElement('h3', { key: 'welcome' }, `Добро пожаловать, ${user?.full_name}!`),
            React.createElement('p', { key: 'role' }, `Роль: ${user?.role === 'teacher' ? 'Преподаватель' : 'Студент'}`),
            user?.role === 'student' && React.createElement('div', { key: 'stats' }, [
              React.createElement('h4', { key: 'stats-title' }, 'Ваша статистика'),
              React.createElement('p', { key: 'stats-count' }, `Всего оценок: ${grades.length}`),
              grades.length > 0 && React.createElement('p', { key: 'stats-avg' }, 
                `Средний балл: ${(grades.reduce((sum, g) => sum + g.grade, 0) / grades.length).toFixed(1)}`
              )
            ])
          ]);
        
        case 'courses':
          return React.createElement('div', null, [
            React.createElement('h3', { key: 'title' }, 'Мои курсы'),
            user?.role === 'teacher' && React.createElement(CreateCourseForm, {
              key: 'create',
              onCourseCreated: loadData
            }),
            courses.length === 0 
              ? React.createElement('p', { key: 'empty' }, 'Нет курсов')
              : React.createElement('div', { key: 'list' },
                  courses.map(course => 
                    React.createElement(CourseCard, {
                      key: course.id,
                      course: course,
                      userRole: user?.role,
                      onEnroll: loadData
                    })
                  )
                )
          ]);
        
        case 'grades':
          return React.createElement('div', null, [
            React.createElement('h3', { key: 'title' }, 'Мои оценки'),
            grades.length === 0
              ? React.createElement('p', { key: 'empty' }, 'Нет оценок')
              : React.createElement('table', { key: 'table' }, [
                  React.createElement('thead', { key: 'head' },
                    React.createElement('tr', null,
                      React.createElement('th', null, 'Курс'),
                      React.createElement('th', null, 'Задание'),
                      React.createElement('th', null, 'Оценка'),
                      React.createElement('th', null, 'Комментарий'),
                      React.createElement('th', null, 'Дата')
                    )
                  ),
                  React.createElement('tbody', { key: 'body' },
                    grades.map(g => 
                      React.createElement('tr', { key: g.assignment_name + g.date },
                        React.createElement('td', null, g.course_name),
                        React.createElement('td', null, g.assignment_name),
                        React.createElement('td', null, `${g.grade}/${g.max_grade}`),
                        React.createElement('td', null, g.feedback || '-'),
                        React.createElement('td', null, new Date(g.graded_at).toLocaleDateString())
                      )
                    )
                  )
                ])
          ]);
        
        default:
          return null;
      }
    };

    return React.createElement('div', { className: 'container' }, [
      React.createElement('div', { key: 'nav', className: 'nav' },
        React.createElement('button', { onClick: () => setCurrentPage('dashboard') }, 'Главная'),
        React.createElement('button', { onClick: () => setCurrentPage('courses') }, 'Курсы'),
        user?.role === 'student' && React.createElement('button', { onClick: () => setCurrentPage('grades') }, 'Мои оценки'),
        React.createElement('button', { onClick: logout }, 'Выйти')
      ),
      React.createElement('div', { key: 'content' }, loading ? 'Загрузка...' : renderContent())
    ]);
  }
};

// Компонент создания курса
function CreateCourseForm({ onCourseCreated }) {
  const [name, setName] = React.useState('');
  const [code, setCode] = React.useState('');
  const [academicYear, setAcademicYear] = React.useState('2025-2026');
  const [semester, setSemester] = React.useState('1');

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      await createCourse({
        name,
        code,
        academic_year: academicYear,
        semester: parseInt(semester)
      });
      setName('');
      setCode('');
      onCourseCreated();
    } catch (error) {
      alert('Ошибка создания курса');
    }
  }

  return React.createElement('form', { onSubmit: handleSubmit, style: { marginBottom: '20px', padding: '10px', background: '#f9f9f9', borderRadius: '4px' } },
    React.createElement('h4', null, 'Создать новый курс'),
    React.createElement('input', {
      placeholder: 'Название курса',
      value: name,
      onChange: (e) => setName(e.target.value),
      required: true
    }),
    React.createElement('input', {
      placeholder: 'Код курса',
      value: code,
      onChange: (e) => setCode(e.target.value),
      required: true
    }),
    React.createElement('select', {
      value: academicYear,
      onChange: (e) => setAcademicYear(e.target.value)
    },
      React.createElement('option', { value: '2024-2025' }, '2024-2025'),
      React.createElement('option', { value: '2025-2026' }, '2025-2026')
    ),
    React.createElement('select', {
      value: semester,
      onChange: (e) => setSemester(e.target.value)
    },
      React.createElement('option', { value: '1' }, 'Семестр 1'),
      React.createElement('option', { value: '2' }, 'Семестр 2')
    ),
    React.createElement('button', { type: 'submit' }, 'Создать курс')
  );
}

// Компонент карточки курса
function CourseCard({ course, userRole, onEnroll }) {
  const [showAssignments, setShowAssignments] = React.useState(false);
  const [assignments, setAssignments] = React.useState([]);

  async function loadAssignments() {
    if (!showAssignments) {
      const data = await getAssignments(course.id);
      setAssignments(data);
    }
    setShowAssignments(!showAssignments);
  }

  async function handleEnroll() {
    try {
      await enrollInCourse(course.id);
      onEnroll();
    } catch (error) {
      alert('Ошибка записи на курс');
    }
  }

  return React.createElement('div', { style: { border: '1px solid #ddd', padding: '10px', margin: '10px 0', borderRadius: '4px' } }, [
    React.createElement('div', { key: 'header', style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' } },
      React.createElement('div', null, [
        React.createElement('h4', { key: 'name' }, course.name),
        React.createElement('p', { key: 'code' }, `Код: ${course.code}`),
        React.createElement('p', { key: 'teacher' }, `Преподаватель: ${course.teacher_id}`),
        React.createElement('p', { key: 'year' }, `${course.academic_year}, семестр ${course.semester}`)
      ]),
      React.createElement('div', null, [
        userRole === 'student' && React.createElement('button', {
          key: 'enroll',
          onClick: handleEnroll,
          style: { marginRight: '10px' }
        }, 'Записаться'),
        React.createElement('button', {
          key: 'toggle',
          onClick: loadAssignments
        }, showAssignments ? 'Скрыть задания' : 'Показать задания')
      ])
    ),
    showAssignments && React.createElement('div', { key: 'assignments', style: { marginTop: '10px', padding: '10px', background: '#f9f9f9' } },
      assignments.length === 0
        ? React.createElement('p', null, 'Нет заданий')
        : assignments.map(a => 
            React.createElement('div', { key: a.id, style: { padding: '5px', borderBottom: '1px solid #eee' } },
              React.createElement('p', null, `${a.title} (макс. ${a.max_grade} баллов)`)
            )
          )
    )
  ]);
}