import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { getParticipants, Participant } from '../api/participants'
import { analyzeAudio } from '../api/analyze'
import AnalysisTimeline from '../components/AnalysisTimeline'
import './AnalyzePage.css'

// UUID generator
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

export default function AnalyzePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [participants, setParticipants] = useState<Participant[]>([])
  const [selectedParticipantId, setSelectedParticipantId] = useState<number | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [progressId, setProgressId] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [loadingParticipants, setLoadingParticipants] = useState(true)
  const [participantsError, setParticipantsError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadParticipants()
    const participantId = searchParams.get('participant_id')
    if (participantId) {
      setSelectedParticipantId(parseInt(participantId))
    }
  }, [searchParams])

  const loadParticipants = async () => {
    setLoadingParticipants(true)
    setParticipantsError(null)
    try {
      const data = await getParticipants()
      setParticipants(data || [])
      if (!data || data.length === 0) {
        setParticipantsError('Henuz kayitli katilimci bulunmamaktadir. Lutfen once katilimci ekleyin.')
      }
    } catch (error: any) {
      console.error('Katilimcilar yuklenirken hata:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Katilimcilar yuklenirken bir hata olustu'
      setParticipantsError(errorMessage)
    } finally {
      setLoadingParticipants(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0])
    }
  }

  const validateAndSetFile = (selectedFile: File) => {
    if (!selectedFile.name.match(/\.(wav|mp3|m4a|webm)$/i)) {
      alert('Desteklenen formatlar: wav, mp3, m4a, webm')
      return
    }
    setFile(selectedFile)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0])
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => {
    setDragOver(false)
  }

  const removeFile = () => {
    setFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedParticipantId) {
      alert('Lutfen bir katilimci secin')
      return
    }
    
    if (!file) {
      alert('Lutfen bir ses dosyasi secin')
      return
    }

    // Progress ID olustur ve SSE baglantisini baslat
    const newProgressId = generateUUID()
    setProgressId(newProgressId)
    setLoading(true)

    try {
      const result = await analyzeAudio(selectedParticipantId, file, newProgressId)
      // Kisa gecikme ile sonuc sayfasina yonlendir
      setTimeout(() => {
        navigate(`/results/${result.id}`)
      }, 1000)
    } catch (error: any) {
      setProgressId(null)
      const errorMessage = error.code === 'ECONNABORTED' 
        ? 'Analiz islemi zaman asimina ugradi. Lutfen tekrar deneyin.'
        : error.response?.data?.detail || error.message || 'Bilinmeyen bir hata olustu'
      alert('Hata: ' + errorMessage)
      console.error('Analiz hatasi:', error)
    } finally {
      setLoading(false)
    }
  }

  const currentStep = !selectedParticipantId ? 1 : !file ? 2 : 3

  return (
    <div className="analyze-page">
      <div className="analyze-header">
        <h1 className="analyze-title">Ses Analizi</h1>
        <p className="analyze-subtitle">Katilimci secin ve ses dosyasini yukleyerek analiz baslatin</p>
      </div>
      
      <form onSubmit={handleSubmit} className="analyze-card">
        {/* Steps indicator */}
        <div className="steps-indicator">
          <div className={`step ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
            <span className="step-number">{currentStep > 1 ? '✓' : '1'}</span>
            <span className="step-label">Katilimci Sec</span>
          </div>
          <div className={`step-connector ${currentStep > 1 ? 'completed' : ''}`}></div>
          <div className={`step ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
            <span className="step-number">{currentStep > 2 ? '✓' : '2'}</span>
            <span className="step-label">Dosya Yukle</span>
          </div>
          <div className={`step-connector ${currentStep > 2 ? 'completed' : ''}`}></div>
          <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>
            <span className="step-number">3</span>
            <span className="step-label">Analiz Et</span>
          </div>
        </div>

        {/* Participant selection */}
        <div className="form-section">
          <h3 className="form-section-title">Katilimci Secimi</h3>
          <div className="form-group">
            <label className="form-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
              </svg>
              Katilimci
            </label>
            {loadingParticipants ? (
              <div className="loading-state">
                <div className="loading-spinner"></div>
                <span>Katilimcilar yukleniyor...</span>
              </div>
            ) : (
              <>
                <select
                  className="form-select"
                  required
                  value={selectedParticipantId || ''}
                  onChange={(e) => setSelectedParticipantId(parseInt(e.target.value))}
                  disabled={participants.length === 0}
                >
                  <option value="">Katilimci secin...</option>
                  {participants.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} - {p.group_type.toUpperCase()} ({p.age} yas)
                    </option>
                  ))}
                </select>
                {participantsError && (
                  <div className="error-message">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/>
                      <line x1="12" x2="12" y1="8" y2="12"/>
                      <line x1="12" x2="12.01" y1="16" y2="16"/>
                    </svg>
                    {participantsError}
                  </div>
                )}
                {participants.length === 0 && !participantsError && (
                  <div className="warning-message">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/>
                      <line x1="12" x2="12" y1="8" y2="12"/>
                      <line x1="12" x2="12.01" y1="16" y2="16"/>
                    </svg>
                    <span>
                      Henuz kayitli katilimci yok. {' '}
                      <Link to="/participants/new">
                        Katilimci eklemek icin tiklayin
                      </Link>
                    </span>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* File upload */}
        <div className="form-section">
          <h3 className="form-section-title">Ses Dosyasi</h3>
          <div className="form-group">
            <div 
              className={`file-upload-zone ${dragOver ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".wav,.mp3,.m4a,.webm"
                onChange={handleFileChange}
              />
              <div className="upload-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17,8 12,3 7,8"/>
                  <line x1="12" x2="12" y1="3" y2="15"/>
                </svg>
              </div>
              <p className="upload-text">
                Dosyayi buraya <strong>surukleyin</strong> veya <strong>tiklayin</strong>
              </p>
              <p className="upload-hint">WAV, MP3, M4A, WEBM - Maks 50MB</p>
            </div>

            {file && (
              <div className="file-info-card">
                <div className="file-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 18V5l12-2v13"/>
                    <circle cx="6" cy="18" r="3"/>
                    <circle cx="18" cy="16" r="3"/>
                  </svg>
                </div>
                <div className="file-details">
                  <p className="file-name">{file.name}</p>
                  <div className="file-meta">
                    <span>{formatFileSize(file.size)}</span>
                    <span>{file.type || 'audio/*'}</span>
                  </div>
                </div>
                <button type="button" className="file-remove" onClick={removeFile}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" x2="6" y1="6" y2="18"/>
                    <line x1="6" x2="18" y1="6" y2="18"/>
                  </svg>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Progress Timeline */}
        {loading && (
          <AnalysisTimeline 
            progressId={progressId} 
            isAnalyzing={loading}
          />
        )}

        {/* Submit */}
        <div className="submit-section">
          <button 
            type="submit" 
            disabled={loading || !selectedParticipantId || !file} 
            className={`btn btn-primary ${loading ? 'btn-loading' : ''}`}
          >
            {!loading && (
              <>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="5,3 19,12 5,21 5,3"/>
                </svg>
                Analizi Baslat
              </>
            )}
          </button>
        </div>
      </form>

      {/* Tips */}
      <div className="tips-section">
        <div className="tips-card">
          <h4 className="tips-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" x2="12" y1="16" y2="12"/>
              <line x1="12" x2="12.01" y1="8" y2="8"/>
            </svg>
            Daha Iyi Sonuclar Icin
          </h4>
          <ul className="tips-list">
            <li>Sessiz bir ortamda kayit yapin</li>
            <li>Net ve anlasilir konusma tercih edin</li>
            <li>Minimum 30 saniye kayit suresi onerilir</li>
            <li>Mikrofonu agziniza yakin tutun</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
