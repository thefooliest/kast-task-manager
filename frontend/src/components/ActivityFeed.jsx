import { useState, useEffect } from 'react';
import { api } from '../api/client';
import styles from '../styles/ActivityFeed.module.css';

const ACTION_ICONS = {
  task_created: '✦',
  task_updated: '✎',
  task_deleted: '✕',
  task_status_changed: '↻',
  task_assigned: '→',
  comment_added: '💬',
  comment_deleted: '✕',
  member_added: '+',
  project_created: '★',
};

export default function ActivityFeed({ projectId }) {
  const [activities, setActivities] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (expanded) {
      loadActivity();
    }
  }, [expanded, projectId]);

  const loadActivity = async () => {
    setLoading(true);
    try {
      const data = await api.getActivity(projectId);
      setActivities(data);
    } catch (err) {
      console.error('Failed to load activity:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={styles.container}>
      <button
        className={styles.toggle}
        onClick={() => setExpanded(!expanded)}
      >
        <span className={styles.toggleIcon}>{expanded ? '▾' : '▸'}</span>
        <span className={styles.title}>Activity</span>
      </button>

      {expanded && (
        <div className={styles.body}>
          {loading ? (
            <div className={styles.loading}>Loading...</div>
          ) : activities.length === 0 ? (
            <div className={styles.empty}>No activity yet.</div>
          ) : (
            <div className={styles.list}>
              {activities.map((a) => (
                <div key={a.id} className={styles.item}>
                  <span className={styles.icon}>
                    {ACTION_ICONS[a.action] || '•'}
                  </span>
                  <div className={styles.content}>
                    <span className={styles.actor}>{a.actor_name}</span>
                    <span className={styles.detail}>{a.detail}</span>
                  </div>
                  <span className={styles.time}>{formatTime(a.created_at)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}