import { useState } from 'react';
import TaskForm from './TaskForm';
import styles from '../styles/TaskItem.module.css';

const STATUS_LABELS = {
  todo: 'To Do',
  in_progress: 'In Progress',
  done: 'Done',
};

const PRIORITY_LABELS = {
  low: 'Low',
  medium: 'Med',
  high: 'High',
};

export default function TaskItem({ task, onUpdate, onDelete }) {
  const [editing, setEditing] = useState(false);

  const handleStatusToggle = () => {
    const next = task.status === 'done' ? 'todo'
      : task.status === 'todo' ? 'in_progress'
      : 'done';
    onUpdate(task.id, { status: next });
  };

  const handleUpdate = (data) => {
    onUpdate(task.id, data);
    setEditing(false);
  };

  if (editing) {
    return (
      <TaskForm
        initial={task}
        onSubmit={handleUpdate}
        onCancel={() => setEditing(false)}
      />
    );
  }

  return (
    <div className={`${styles.item} ${task.status === 'done' ? styles.done : ''}`}>
      <button
        className={`${styles.checkbox} ${styles[task.status]}`}
        onClick={handleStatusToggle}
        title={`Status: ${STATUS_LABELS[task.status]}`}
      >
        {task.status === 'done' && '✓'}
        {task.status === 'in_progress' && '•'}
      </button>

      <div className={styles.content}>
        <span className={styles.title}>{task.title}</span>
        {task.description && (
          <span className={styles.description}>{task.description}</span>
        )}
      </div>

      <span className={`${styles.priority} ${styles[`priority_${task.priority}`]}`}>
        {PRIORITY_LABELS[task.priority]}
      </span>

      <div className={styles.actions}>
        <button className="btn btn-ghost" onClick={() => setEditing(true)}>
          Edit
        </button>
        <button className="btn btn-danger" onClick={() => onDelete(task.id)}>
          Delete
        </button>
      </div>
    </div>
  );
}