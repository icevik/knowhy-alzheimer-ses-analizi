import { useEffect, useState } from 'react'
import { getAllAnalyses, getAnalysisResult, deleteAnalysis, AnalysisListItem, AnalysisResult } from '../api/analyze'
import { getParticipant, Participant } from '../api/participants'
import Modal from './Modal'
import './HistoryModal.css'

interface HistoryModalProps {
  isOpen: boolean
  onClose: () => void
  onViewDetails: (analysisId: number) => void
}

export default function HistoryModal({ isOpen, onClose, onViewDetails }: HistoryModalProps) {
  const [analyses, setAnalyses] = useState<AnalysisListItem[]>([])
  const [participants, setParticipants] = useState<Record<number, Participant>>({})
  const [loading, setLoading] = useState(true)
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisResult | null>(null)
  const [showDetails, setShowDetails] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadAnalyses()
    } else {
      setSelectedAnalysis(null)
      setShowDetails(false)
    }
  }, [isOpen])

  const loadAnalyses = async () => {
    setLoading(true)
    try {
      const data = await getAllAnalyses(100, 0)
      setAnalyses(data.items)
      
      // Participant bilgilerini yükle
      const participantIds = [...new Set(data.items.map(a => a.participant_id))]
      const participantMap: Record<number, Participant> = {}
      
      await Promise.all(
        participantIds.map(async (id) => {
          try {
            const participant = await getParticipant(id)
            participantMap[id] = participant
          } catch (error) {
            console.error(`Participant ${id} yüklenemedi:`, error)
          }
        })
      )
      
      setParticipants(participantMap)
    } catch (error) {
      console.error('Analizler yüklenirken hata:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleViewDetails = async (analysisId: number) => {
    try {
      const result = await getAnalysisResult(analysisId)
      setSelectedAnalysis(result)
      setShowDetails(true)
    } catch (error) {
      console.error('Analiz detayı yüklenirken hata:', error)
    }
  }

  const handleDelete = async (analysisId: number, event: React.MouseEvent) => {
    event.stopPropagation()
    
    if (!confirm('Bu analizi silmek istediginizden emin misiniz? Bu islem geri alinamaz.')) {
      return
    }
    
    setDeletingId(analysisId)
    try {
      await deleteAnalysis(analysisId)
      // Listeyi güncelle
      setAnalyses(prev => prev.filter(a => a.id !== analysisId))
    } catch (error) {
      console.error('Analiz silinirken hata:', error)
      alert('Analiz silinirken bir hata olustu. Lutfen tekrar deneyin.')
    } finally {
      setDeletingId(null)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('tr-TR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  const getGroupColor = (groupType: string) => {
    switch (groupType) {
      case 'alzheimer': return 'var(--alzheimer-color)'
      case 'mci': return 'var(--mci-color)'
      case 'control': return 'var(--control-color)'
      default: return 'var(--text-muted)'
    }
  }

  if (showDetails && selectedAnalysis) {
    return (
      <Modal
        isOpen={isOpen}
        onClose={() => {
          setShowDetails(false)
          setSelectedAnalysis(null)
        }}
        title="Analiz Detaylari"
        size="xlarge"
      >
        <div className="history-details">
          <div className="details-section">
            <h3 className="details-section-title">Katilimci Bilgileri</h3>
            {participants[selectedAnalysis.participant_id] && (
              <div className="participant-info">
                <div className="info-item">
                  <span className="info-label">Ad Soyad:</span>
                  <span className="info-value">{participants[selectedAnalysis.participant_id].name}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Yas:</span>
                  <span className="info-value">{participants[selectedAnalysis.participant_id].age}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Grup:</span>
                  <span 
                    className="info-value group-badge"
                    style={{ color: getGroupColor(participants[selectedAnalysis.participant_id].group_type) }}
                  >
                    {participants[selectedAnalysis.participant_id].group_type.toUpperCase()}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="details-section">
            <h3 className="details-section-title">Transkript</h3>
            <div className="transcript-preview">
              {selectedAnalysis.transcript}
            </div>
          </div>

          <div className="details-grid">
            <div className="details-card">
              <h4 className="card-title">Duygu Analizi</h4>
              <div className="card-content">
                <div className="metric">
                  <span className="metric-label">Ton</span>
                  <span className="metric-value">{selectedAnalysis.emotion_analysis.tone}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Yogunluk</span>
                  <span className="metric-value">{selectedAnalysis.emotion_analysis.intensity}/10</span>
                </div>
                <div className="emotions-list">
                  {selectedAnalysis.emotion_analysis.emotions.map((emotion, idx) => (
                    <span key={idx} className="emotion-badge">{emotion}</span>
                  ))}
                </div>
              </div>
            </div>

            <div className="details-card">
              <h4 className="card-title">Icerik Analizi</h4>
              <div className="card-content">
                <div className="metric">
                  <span className="metric-label">Kelime Sayisi</span>
                  <span className="metric-value">{selectedAnalysis.content_analysis.word_count}</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Akicilik</span>
                  <span className="metric-value">{selectedAnalysis.content_analysis.fluency_score}/10</span>
                </div>
                <div className="metric">
                  <span className="metric-label">Tutarlilik</span>
                  <span className="metric-value">{selectedAnalysis.content_analysis.coherence_score}/10</span>
                </div>
              </div>
            </div>
          </div>

          <div className="details-actions">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setShowDetails(false)
                setSelectedAnalysis(null)
              }}
            >
              Geri Don
            </button>
            <button
              className="btn btn-primary"
              onClick={() => {
                onViewDetails(selectedAnalysis.id)
                onClose()
              }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              Tam Detaylari Goruntule
            </button>
          </div>
        </div>
      </Modal>
    )
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Gecmis Kayitlar"
      size="large"
    >
      <div className="history-modal">
        {loading ? (
          <div className="history-loading">
            <div className="loading-spinner"></div>
            <span>Kayitlar yukleniyor...</span>
          </div>
        ) : analyses.length === 0 ? (
          <div className="history-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
              <polyline points="14,2 14,8 20,8"/>
            </svg>
            <p>Henuz kayit bulunmuyor</p>
          </div>
        ) : (
          <div className="history-list">
            {analyses.map((analysis) => {
              const participant = participants[analysis.participant_id]
              return (
                <div key={analysis.id} className="history-item">
                  <div className="history-item-header">
                    <div className="history-item-info">
                      <h4 className="history-item-title">
                        Analiz #{analysis.id}
                      </h4>
                      {participant && (
                        <div className="history-item-meta">
                          <span className="participant-name">{participant.name}</span>
                          <span className="meta-separator">•</span>
                          <span 
                            className="group-tag"
                            style={{ color: getGroupColor(participant.group_type) }}
                          >
                            {participant.group_type.toUpperCase()}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="history-item-date">
                      {formatDate(analysis.created_at)}
                    </div>
                  </div>
                  
                  <div className="history-item-preview">
                    <p className="transcript-preview-text">
                      {analysis.transcript}
                    </p>
                  </div>

                  <div className="history-item-stats">
                    <div className="stat-badge">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                      </svg>
                      {analysis.emotion_analysis.tone}
                    </div>
                    <div className="stat-badge">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                      </svg>
                      {analysis.content_analysis.word_count} kelime
                    </div>
                    <div className="stat-badge">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                      </svg>
                      Akicilik: {analysis.content_analysis.fluency_score}/10
                    </div>
                  </div>

                  <div className="history-item-actions">
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleViewDetails(analysis.id)}
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                      </svg>
                      Detaylar
                    </button>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => {
                        onViewDetails(analysis.id)
                        onClose()
                      }}
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="9,18 15,12 9,6"/>
                      </svg>
                      Tam Sayfa
                    </button>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={(e) => handleDelete(analysis.id, e)}
                      disabled={deletingId === analysis.id}
                    >
                      {deletingId === analysis.id ? (
                        <span className="loading-spinner-small"></span>
                      ) : (
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="3,6 5,6 21,6"/>
                          <path d="M19,6v14a2,2 0,0,1 -2,2H7a2,2 0,0,1 -2,-2V6m3,0V4a2,2 0,0,1 2,-2h4a2,2 0,0,1 2,2v2"/>
                        </svg>
                      )}
                      Sil
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </Modal>
  )
}

