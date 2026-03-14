import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
import MemberList from '../components/MemberList';
import TaskForm from '../components/TaskForm';
import TaskItem from '../components/TaskItem';
import { useAuth } from '../context/AuthContext';
import styles from '../styles/TasksPage.module.css';

const STATUS_FILTERS = [
  { value: null, label: 'All' },
  { value: 'todo', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'done', label: 'Done' },
];

const TASKS_PER_PAGE = 20;

export default function TasksPage() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState(null);

  const isOwner = project && user && project.owner_id === user.id;

  useEffect(() => {
    loadProject();
  }, [projectId]);

  useEffect(() => {
    setOffset(0);
    loadTasks(0);
  }, [projectId, statusFilter]);

  const loadProject = async () => {
    try {
      const data = await api.getProject(projectId);
      setProject(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const loadTasks = async (newOffset = offset) => {
    try {
      const data = await api.getTasks(projectId, statusFilter, TASKS_PER_PAGE, newOffset);
      setTasks(data.tasks);
      setTotal(data.total);
      setOffset(newOffset);
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
      loadTasks(0);
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

  const hasMore = offset + TASKS_PER_PAGE < total;
  const hasPrev = offset > 0;
  const currentPage = Math.floor(offset / TASKS_PER_PAGE) + 1;
  const totalPages = Math.ceil(total / TASKS_PER_PAGE);

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

      <MemberList projectId={projectId} isOwner={isOwner} />

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
          {total} task{total !== 1 ? 's' : ''}
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

      {totalPages > 1 && (
        <div className={styles.pagination}>
          <button
            className="btn btn-secondary"
            onClick={() => loadTasks(offset - TASKS_PER_PAGE)}
            disabled={!hasPrev}
          >
            ← Previous
          </button>
          <span className={styles.pageInfo}>
            Page {currentPage} of {totalPages}
          </span>
          <button
            className="btn btn-secondary"
            onClick={() => loadTasks(offset + TASKS_PER_PAGE)}
            disabled={!hasMore}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}