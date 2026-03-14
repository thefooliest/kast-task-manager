import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import styles from '../styles/ProjectsPage.module.css';

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await api.getProjects();
      setProjects(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await api.createProject(name, description || null);
      setName('');
      setDescription('');
      setShowForm(false);
      loadProjects();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return <div className={styles.loading}>Loading projects...</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>My Projects</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancel' : '+ New Project'}
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {showForm && (
        <form onSubmit={handleCreate} className={styles.form}>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Project name"
            required
            autoFocus
          />
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optional)"
          />
          <button type="submit" className="btn btn-primary">
            Create Project
          </button>
        </form>
      )}

      {projects.length === 0 && !showForm ? (
        <div className={styles.empty}>
          <p>No projects yet.</p>
          <p>Create your first project to get started.</p>
        </div>
      ) : (
        <div className={styles.list}>
          {projects.map((project) => (
            <div
              key={project.id}
              className={styles.card}
              onClick={() => navigate(`/projects/${project.id}/tasks`)}
            >
              <h3 className={styles.cardTitle}>{project.name}</h3>
              {project.description && (
                <p className={styles.cardDesc}>{project.description}</p>
              )}
              <span className={styles.cardArrow}>→</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}