import { useState, useEffect } from 'react';
import { api } from '../api/client';
import styles from '../styles/MemberList.module.css';

export default function MemberList({ projectId, isOwner, onMembersLoaded }) {
  const [members, setMembers] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMembers();
  }, [projectId]);

  const loadMembers = async () => {
    try {
      const data = await api.getProjectMembers(projectId);
      setMembers(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.addProjectMember(projectId, email);
      setEmail('');
      setShowAdd(false);
      loadMembers();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return null;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Members ({members.length})</h3>
        {isOwner && (
          <button
            className="btn btn-ghost"
            onClick={() => setShowAdd(!showAdd)}
          >
            {showAdd ? 'Cancel' : '+ Add'}
          </button>
        )}
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {showAdd && (
        <form onSubmit={handleAdd} className={styles.addForm}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="user@example.com"
            required
            autoFocus
          />
          <button type="submit" className="btn btn-primary">
            Add
          </button>
        </form>
      )}

      <div className={styles.list}>
        {members.map((m) => (
          <div key={m.user_id} className={styles.member}>
            <span className={styles.dot} />
            <div className={styles.memberInfo}>
              <span className={styles.memberName}>{m.full_name}</span>
              <span className={styles.memberEmail}>{m.email}</span>
            </div>
            <span className={`${styles.role} ${styles[m.role]}`}>
              {m.role}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}