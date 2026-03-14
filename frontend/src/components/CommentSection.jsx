import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import styles from '../styles/CommentSection.module.css';

export default function CommentSection({ projectId, taskId }) {
  const { user } = useAuth();
  const [comments, setComments] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (expanded) {
      loadComments();
    }
  }, [expanded, projectId, taskId]);

  const loadComments = async () => {
    setLoading(true);
    try {
      const data = await api.getComments(projectId, taskId);
      setComments(data);
      setCount(data.length);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) return;
    setError('');
    try {
      await api.createComment(projectId, taskId, content.trim());
      setContent('');
      loadComments();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (commentId) => {
    try {
      await api.deleteComment(projectId, taskId, commentId);
      loadComments();
    } catch (err) {
      setError(err.message);
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
        <span className={styles.icon}>{expanded ? '▾' : '▸'}</span>
        <span>Comments{count > 0 ? ` (${count})` : ''}</span>
      </button>

      {expanded && (
        <div className={styles.body}>
          {error && <div className={styles.error}>{error}</div>}

          {loading ? (
            <div className={styles.loading}>Loading...</div>
          ) : (
            <>
              {comments.length > 0 && (
                <div className={styles.list}>
                  {comments.map((c) => (
                    <div key={c.id} className={styles.comment}>
                      <div className={styles.commentHeader}>
                        <span className={styles.author}>{c.author_name}</span>
                        <span className={styles.time}>{formatTime(c.created_at)}</span>
                        {(c.user_id === user?.id) && (
                          <button
                            className={styles.deleteBtn}
                            onClick={() => handleDelete(c.id)}
                            title="Delete comment"
                          >
                            ×
                          </button>
                        )}
                      </div>
                      <p className={styles.content}>{c.content}</p>
                    </div>
                  ))}
                </div>
              )}

              <form onSubmit={handleSubmit} className={styles.form}>
                <input
                  type="text"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Write a comment..."
                  className={styles.input}
                />
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={!content.trim()}
                >
                  Post
                </button>
              </form>
            </>
          )}
        </div>
      )}
    </div>
  );
}