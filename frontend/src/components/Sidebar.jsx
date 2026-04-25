export default function Sidebar({ sessions, activeSessionId, open, onToggle, onSelect, onNewChat, onDelete, onClearAll, user, onLogout }) {
  return (
    <>
      <button className={`sidebar-toggle ${open ? 'hidden' : ''}`} onClick={onToggle}>
        ☰
      </button>

      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="sidebar-top">
          <div className="sidebar-top-row">
            <h2>⚖️ Nepal Law AI Assistant</h2>
            <button className="sidebar-close" onClick={onToggle}>✕</button>
          </div>
          <button className="new-chat-btn" onClick={onNewChat}>＋ New Chat</button>
        </div>

        <div className="sidebar-history">
          <h3>Chat History</h3>
          {sessions.length === 0 && <p className="no-history">No conversations yet</p>}
          {sessions.map((session) => (
            <div key={session.id} className={`history-item${activeSessionId === session.id ? ' active' : ''}`}>
              <div className="history-item-text" onClick={() => onSelect(session)} title={session.title}>
                <span className="history-q">{session.title.length > 38 ? session.title.slice(0, 38) + '…' : session.title}</span>
                <span className="history-date">
                  {new Date(session.updated_at || session.created_at).toLocaleDateString()}
                </span>
              </div>
              <button
                className="history-delete"
                onClick={(e) => { e.stopPropagation(); onDelete(session.id); }}
                title="Delete"
              >
                🗑
              </button>
            </div>
          ))}
          {sessions.length > 0 && (
            <button className="clear-all-btn" onClick={onClearAll}>
              🗑 Clear all chats
            </button>
          )}
        </div>

        <div className="sidebar-bottom">
          <div className="user-info">
            <div className="user-avatar">{user?.name?.charAt(0).toUpperCase()}</div>
            <span className="user-name">{user?.name}</span>
          </div>
          <button className="logout-btn" onClick={onLogout}>Sign Out</button>
        </div>
      </aside>
    </>
  )
}
