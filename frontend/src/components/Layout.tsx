import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import HistoryModal from './HistoryModal'
import { useAuth } from '../context/AuthContext'
import './Layout.css'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [showHistory, setShowHistory] = useState(false)

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/': return 'Dashboard'
      case '/participants/new': return 'Yeni Katilimci'
      case '/analyze': return 'Ses Analizi'
      default:
        if (location.pathname.startsWith('/results')) return 'Analiz Sonuclari'
        return 'Dashboard'
    }
  }

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon">
              <img src="/logo.png" alt="Logo" className="logo-img" />
            </div>
            <div className="logo-text">
              <span className="logo-title">Alzheimer Analizi Projesi</span>
              <a href="https://www.knowhy.co" target="_blank" rel="noopener noreferrer" className="logo-subtitle hover-link">
                Powered by KNOWHY
              </a>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <span className="nav-section-title">Ana Menu</span>

          <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" rx="1" />
              <rect x="14" y="3" width="7" height="7" rx="1" />
              <rect x="3" y="14" width="7" height="7" rx="1" />
              <rect x="14" y="14" width="7" height="7" rx="1" />
            </svg>
            <span>Dashboard</span>
          </Link>

          <span className="nav-section-title">Islemler</span>

          <Link to="/participants/new" className={`nav-link ${isActive('/participants') ? 'active' : ''}`}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <line x1="19" x2="19" y1="8" y2="14" />
              <line x1="22" x2="16" y1="11" y2="11" />
            </svg>
            <span>Yeni Katilimci</span>
          </Link>

          <Link to="/analyze" className={`nav-link ${isActive('/analyze') ? 'active' : ''}`}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" x2="12" y1="19" y2="22" />
            </svg>
            <span>Ses Analizi</span>
          </Link>

          <span className="nav-section-title">Raporlar</span>

          <button
            className="nav-link"
            onClick={() => setShowHistory(true)}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
              <polyline points="14,2 14,8 20,8" />
              <line x1="16" x2="8" y1="13" y2="13" />
              <line x1="16" x2="8" y1="17" y2="17" />
              <line x1="10" x2="8" y1="9" y2="9" />
            </svg>
            <span>Gecmis Kayitlar</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          {user && (
            <div className="user-info">
              <div className="user-avatar">
                {user.email.charAt(0).toUpperCase()}
              </div>
              <div className="user-details">
                <span className="user-email">{user.email}</span>
                <button className="logout-btn" onClick={logout}>
                  Çıkış Yap
                </button>
              </div>
            </div>
          )}
          <div className="version-info">
            <span className="version-dot"></span>
            <span>v1.0.0 - Aktif</span>
          </div>
        </div>
      </aside>

      {/* Main wrapper */}
      <div className="main-wrapper">
        {/* Top bar */}
        <header className="topbar">
          <div className="topbar-left">
            <nav className="breadcrumb">
              <span>Ana Sayfa</span>
              <span className="breadcrumb-separator">/</span>
              <span className="breadcrumb-current">{getPageTitle()}</span>
            </nav>
          </div>
          <div className="topbar-right">
            <button className="topbar-btn" title="Bildirimler">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
            </button>
            <button className="topbar-btn" title="Ayarlar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
              </svg>
            </button>
          </div>
        </header>

        {/* Main content */}
        <main className="main-content">
          {children}
        </main>

        {/* Footer */}
        <footer className="main-footer">
          <div className="footer-content">
            <span>Made with <span className="heart">❤</span></span>
            <span className="footer-divider">•</span>
            <a href="https://www.knowhy.co" target="_blank" rel="noopener noreferrer" className="footer-link">
              Powered by KNOWHY
            </a>
          </div>
        </footer>
      </div>

      <HistoryModal
        isOpen={showHistory}
        onClose={() => setShowHistory(false)}
        onViewDetails={(analysisId) => {
          setShowHistory(false)
          navigate(`/results/${analysisId}`)
        }}
      />
    </div>
  )
}
