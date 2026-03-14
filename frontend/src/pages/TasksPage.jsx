import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
import TaskForm from '../components/TaskForm';
import TaskItem from '../components/TaskItem';
import styles from '../styles/TasksPage.module.css';

const STATUS_FILTERS = [
  { value: null, label: 'All' },
  { value: 'todo', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'done', label: 'Done' },
];

export default function TasksPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState(null);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  useEffect(() => {
    loadTasks();
  }, [projectId, statusFilter]);

  const loadProject = async () => {
    try {
      const data = await api.getProject(projectId);
      setProject(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const loadTasks = async () => {
    try {
      const data = await api.getTasks(projectId, statusFilter);
      setTasks(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (data) => {
    try {
      await api.createTask(projectId, data);
      setShowForm(false);
      loadTasks();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleUpdate = async (taskId, data) => {
    try {
      await api.updateTask(projectId, taskId, data);
      loadTasks();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (taskId) => {
    try {
      await api.deleteTask(projectId, taskId);
      loadTasks();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return <div className={styles.loading}>Loading tasks...</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>{project?.name || 'Project'}</h2>
          {project?.description && (
            <p className={styles.description}>{project.description}</p>
          )}
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancel' : '+ Add Task'}
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {showForm && (
        <div className={styles.formWrapper}>
          <TaskForm onSubmit={handleCreate} onCancel={() => setShowForm(false)} />
        </div>
      )}

      <div className={styles.filters}>
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.value || 'all'}
            className={`${styles.filterBtn} ${statusFilter === f.value ? styles.filterActive : ''}`}
            onClick={() => setStatusFilter(f.value)}
          >
            {f.label}
          </button>
        ))}
        <span className={styles.count}>
          {tasks.length} task{tasks.length !== 1 ? 's' : ''}
        </span>
      </div>

      {tasks.length === 0 ? (
        <div className={styles.empty}>
          <p>
            {statusFilter
              ? 'No tasks match this filter.'
              : 'No tasks yet. Add your first task to get started.'}
          </p>
        </div>
      ) : (
        <div className={styles.list}>
          {tasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}