import { useState } from 'react';
import styles from '../styles/TaskForm.module.css';

export default function TaskForm({ onSubmit, onCancel, initial = null, members = [] }) {
  const [title, setTitle] = useState(initial?.title || '');
  const [description, setDescription] = useState(initial?.description || '');
  const [priority, setPriority] = useState(initial?.priority || 'medium');
  const [status, setStatus] = useState(initial?.status || 'todo');
  const [assignedTo, setAssignedTo] = useState(initial?.assigned_to || '');

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = {
      title,
      description: description || null,
      priority,
      assigned_to: assignedTo || null,
    };
    if (initial) {
      data.status = status;
    }
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Task title"
        required
        autoFocus
      />
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Description (optional)"
        rows={2}
      />
      <div className={styles.row}>
        <div className={styles.field}>
          <label>Priority</label>
          <select value={priority} onChange={(e) => setPriority(e.target.value)}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
        {initial && (
          <div className={styles.field}>
            <label>Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="todo">To Do</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
            </select>
          </div>
        )}
        <div className={styles.field}>
          <label>Assign to</label>
          <select value={assignedTo} onChange={(e) => setAssignedTo(e.target.value)}>
            <option value="">Unassigned</option>
            {members.map((m) => (
              <option key={m.user_id} value={m.user_id}>
                {m.full_name}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className={styles.actions}>
        <button type="button" className="btn btn-ghost" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary">
          {initial ? 'Update' : 'Add Task'}
        </button>
      </div>
    </form>
  );
}