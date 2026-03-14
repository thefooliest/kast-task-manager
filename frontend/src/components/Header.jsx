import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import styles from '../styles/Header.module.css';

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <div className={styles.left}>
          <h1
            className={styles.logo}
            onClick={() => navigate('/projects')}
          >
            Tasks
          </h1>
          {location.pathname !== '/projects' && (
            <button
              className="btn btn-ghost"
              onClick={() => navigate('/projects')}
            >
              ← Projects
            </button>
          )}
        </div>
        <div className={styles.right}>
          <span className={styles.userName}>{user.fullName}</span>
          <button className="btn btn-ghost" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </div>
    </header>
  );
}