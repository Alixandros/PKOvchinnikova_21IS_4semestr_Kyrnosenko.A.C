function App() {
  const [user, setUser] = React.useState(null);
  const [token, setToken] = React.useState(localStorage.getItem('token'));
  const [currentPage, setCurrentPage] = React.useState('dashboard');

  React.useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    }
  }, [token]);

  async function fetchUser() {
    try {
      const response = await api.get('/users/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    }
  }

  async function handleLogin(email, password) {
    try {
      const data = await login(email, password);
      localStorage.setItem('token', data.access_token);
      api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
      await fetchUser();
      setCurrentPage('dashboard');
      return true;
    } catch (error) {
      alert('Ошибка входа: ' + (error.response?.data?.detail || 'Неизвестная ошибка'));
      return false;
    }
  }

  async function handleRegister(userData) {
    try {
      await register(userData);
      alert('Регистрация успешна! Теперь войдите в систему.');
      setCurrentPage('login');
      return true;
    } catch (error) {
      alert('Ошибка регистрации: ' + (error.response?.data?.detail || 'Неизвестная ошибка'));
      return false;
    }
  }

  function logout() {
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
    setToken(null);
    setCurrentPage('login');
  }

  if (!token) {
    return (
      <Pages.Auth 
        onLogin={handleLogin} 
        onRegister={handleRegister}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
      />
    );
  }

  return (
    <Pages.Dashboard 
      user={user} 
      logout={logout}
      currentPage={currentPage}
      setCurrentPage={setCurrentPage}
    />
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(React.createElement(App));