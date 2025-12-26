import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { getAnalysisResult, AnalysisResult } from '../api/analyze'
import { downloadReportPdf } from '../api/reports'
import './ResultsPage.css'

export default function ResultsPage() {
  const { analysisId } = useParams<{ analysisId: string }>()
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloadingPdf, setDownloadingPdf] = useState(false)

  useEffect(() => {
    if (analysisId) {
      loadResult(parseInt(analysisId))
    }
  }, [analysisId])

  const loadResult = async (id: number) => {
    try {
      const data = await getAnalysisResult(id)
      setResult(data)
    } catch (error) {
      console.error('Sonuc yuklenirken hata:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadPdf = async () => {
    if (!result || !result.report_pdf_path) return
    
    setDownloadingPdf(true)
    try {
      const blob = await downloadReportPdf(result.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `rapor_${result.id}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('PDF indirme hatasi:', error)
      alert('PDF indirilirken hata olustu')
    } finally {
      setDownloadingPdf(false)
    }
  }

  if (loading) {
    return (
      <div className="results-loading">
        <div className="loading-spinner"></div>
        <span>Sonuclar yukleniyor...</span>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="results-error">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" x2="12" y1="8" y2="12"/>
          <line x1="12" x2="12.01" y1="16" y2="16"/>
        </svg>
        <span>Sonuc bulunamadi</span>
      </div>
    )
  }

  return (
    <div className="results-page">
      <div className="results-header">
        <h1 className="results-title">Analiz Sonuclari</h1>
        <p className="results-subtitle">Ses dosyanizin detayli analiz raporu</p>
        {result.report_pdf_path && (
          <button 
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
            className="btn btn-primary"
            style={{ marginTop: '1rem' }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17,8 12,3 7,8"/>
              <line x1="12" x2="12" y1="3" y2="15"/>
            </svg>
            {downloadingPdf ? 'Indiriliyor...' : 'PDF Raporu Indir'}
          </button>
        )}
      </div>

      <div className="results-grid">
        {/* Transcript Section */}
        <div className="results-section">
          <div className="section-header">
            <div className="section-icon transcript">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" x2="8" y1="13" y2="13"/>
                <line x1="16" x2="8" y1="17" y2="17"/>
              </svg>
            </div>
            <div className="section-title-group">
              <h2 className="section-title">Transkript</h2>
              <p className="section-description">Konusmanin metne donusturulmus hali</p>
            </div>
          </div>
          <div className="section-content">
            <div className="transcript-box">
              <p className="transcript-text">{result.transcript || 'Transkript bulunamadi'}</p>
            </div>
          </div>
        </div>

        {/* Emotion Analysis Section */}
        <div className="results-section">
          <div className="section-header">
            <div className="section-icon emotion">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
                <line x1="9" x2="9.01" y1="9" y2="9"/>
                <line x1="15" x2="15.01" y1="9" y2="9"/>
              </svg>
            </div>
            <div className="section-title-group">
              <h2 className="section-title">Duygu Analizi</h2>
              <p className="section-description">Ses tonundan tespit edilen duygusal durumlar</p>
            </div>
          </div>
          <div className="section-content">
            <div className="analysis-grid">
              <div className="analysis-item">
                <p className="analysis-label">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                  </svg>
                  Ton
                </p>
                <p className="analysis-value">{result.emotion_analysis.tone}</p>
              </div>
              <div className="analysis-item">
                <p className="analysis-label">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                  </svg>
                  Yogunluk
                </p>
                <p className="analysis-value">{result.emotion_analysis.intensity}<span style={{fontSize: '1rem', color: 'var(--text-muted)'}}>/10</span></p>
                <div className="score-meter">
                  <div className="score-bar-container">
                    <div 
                      className="score-bar tertiary" 
                      style={{width: `${result.emotion_analysis.intensity * 10}%`}}
                    ></div>
                  </div>
                </div>
              </div>
              <div className="analysis-item" style={{gridColumn: 'span 2'}}>
                <p className="analysis-label">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                  </svg>
                  Duygular
                </p>
                <div className="emotion-tags">
                  {result.emotion_analysis.emotions.map((emotion, idx) => (
                    <span key={idx} className="emotion-tag">{emotion}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Content Analysis Section */}
        <div className="results-section">
          <div className="section-header">
            <div className="section-icon content">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
            </div>
            <div className="section-title-group">
              <h2 className="section-title">Icerik Analizi</h2>
              <p className="section-description">Konusma iceriginin dilbilimsel analizi</p>
            </div>
          </div>
          <div className="section-content">
            <div className="analysis-grid">
              <div className="analysis-item">
                <p className="analysis-label">Kelime Sayisi</p>
                <p className="analysis-value">
                  {result.content_analysis?.word_count || result.linguistic_analysis?.word_count || 0}
                </p>
              </div>
              <div className="analysis-item">
                <p className="analysis-label">Benzersiz Kelime</p>
                <p className="analysis-value">
                  {result.content_analysis?.unique_words || result.linguistic_analysis?.unique_word_count || 0}
                </p>
              </div>
              <div className="analysis-item">
                <p className="analysis-label">Akicilik Skoru</p>
                {(() => {
                  // Fluency: content_analysis varsa kullan, yoksa hesitation_ratio'dan hesapla
                  let fluency = result.content_analysis?.fluency_score ?? 0;
                  if (!fluency && result.linguistic_analysis?.hesitation_ratio !== undefined) {
                    // Düşük duraklatma oranı = yüksek akıcılık
                    fluency = Math.round((1 - Math.min(result.linguistic_analysis.hesitation_ratio * 5, 1)) * 10);
                  }
                  return (
                    <>
                      <p className="analysis-value">{fluency}<span style={{fontSize: '1rem', color: 'var(--text-muted)'}}>/10</span></p>
                      <div className="score-meter">
                        <div className="score-bar-container">
                          <div className="score-bar primary" style={{width: `${fluency * 10}%`}}></div>
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>
              <div className="analysis-item">
                <p className="analysis-label">Tutarlilik Skoru</p>
                {(() => {
                  // Coherence: content_analysis varsa kullan, yoksa repetition_ratio'dan hesapla
                  let coherence = result.content_analysis?.coherence_score ?? 0;
                  if (!coherence && result.linguistic_analysis?.repetition_ratio !== undefined) {
                    // Düşük tekrar oranı = yüksek tutarlılık
                    coherence = Math.round((1 - Math.min(result.linguistic_analysis.repetition_ratio * 10, 1)) * 10);
                  }
                  return (
                    <>
                      <p className="analysis-value">{coherence}<span style={{fontSize: '1rem', color: 'var(--text-muted)'}}>/10</span></p>
                      <div className="score-meter">
                        <div className="score-bar-container">
                          <div className="score-bar secondary" style={{width: `${coherence * 10}%`}}></div>
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>
            </div>
          </div>
        </div>

        {/* Advanced Acoustic Features Section */}
        {result.advanced_acoustic && (
          <div className="results-section">
            <div className="section-header">
              <div className="section-icon acoustic">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 18V5l12-2v13"/>
                  <circle cx="6" cy="18" r="3"/>
                  <circle cx="18" cy="16" r="3"/>
                </svg>
              </div>
              <div className="section-title-group">
                <h2 className="section-title">Gelismis Akustik Ozellikler</h2>
                <p className="section-description">Ses kalitesi ve konusma akisi metrikleri</p>
              </div>
            </div>
            <div className="section-content">
              <div className="analysis-grid">
                <div className="analysis-item">
                  <p className="analysis-label">Jitter (Local)</p>
                  <p className="analysis-value">{result.advanced_acoustic.jitter.local.toFixed(4)}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">Shimmer (Local)</p>
                  <p className="analysis-value">{result.advanced_acoustic.shimmer.local.toFixed(4)}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">HNR (dB)</p>
                  <p className="analysis-value">{result.advanced_acoustic.hnr.toFixed(2)}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">F1 Formant (Hz)</p>
                  <p className="analysis-value">{result.advanced_acoustic.formants.F1.toFixed(2)}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">F2 Formant (Hz)</p>
                  <p className="analysis-value">{result.advanced_acoustic.formants.F2.toFixed(2)}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">Duraklama Sayisi</p>
                  <p className="analysis-value">{result.advanced_acoustic.pause_analysis.pause_count}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">Ort. Duraklama (sn)</p>
                  <p className="analysis-value">{result.advanced_acoustic.pause_analysis.avg_pause_duration.toFixed(2)}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">Duraklama %</p>
                  <p className="analysis-value">{result.advanced_acoustic.pause_analysis.pause_percentage.toFixed(1)}%</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Linguistic Analysis Section */}
        {result.linguistic_analysis && (
          <div className="results-section">
            <div className="section-header">
              <div className="section-icon content">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                </svg>
              </div>
              <div className="section-title-group">
                <h2 className="section-title">Dilbilimsel Analiz</h2>
                <p className="section-description">Kelime cesitliligi ve konusma yapisi</p>
              </div>
            </div>
            <div className="section-content">
              <div className="analysis-grid">
                <div className="analysis-item">
                  <p className="analysis-label">Type-Token Ratio</p>
                  <p className="analysis-value">{result.linguistic_analysis.type_token_ratio.toFixed(3)}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">Cesitlilik Skoru</p>
                  <p className="analysis-value">{result.linguistic_analysis.diversity_score.toFixed(1)}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">Ort. Cumle Uzunlugu</p>
                  <p className="analysis-value">{result.linguistic_analysis.mean_length_utterance.toFixed(2)}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">Cumle Sayisi</p>
                  <p className="analysis-value">{result.linguistic_analysis.sentence_count}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">Hesitation Sayisi</p>
                  <p className="analysis-value">{result.linguistic_analysis.hesitation_count}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">Tekrar Sayisi</p>
                  <p className="analysis-value">{result.linguistic_analysis.repetition_count}</p>
                </div>
                <div className="analysis-item">
                  <p className="analysis-label">Sozdizimsel Karmasiklik</p>
                  <p className="analysis-value">{result.linguistic_analysis.syntactic_complexity.toUpperCase()}</p>
                </div>
                {result.linguistic_analysis.hesitation_markers.length > 0 && (
                  <div className="analysis-item" style={{gridColumn: 'span 2'}}>
                    <p className="analysis-label">Hesitation Marker'lar</p>
                    <div className="emotion-tags">
                      {result.linguistic_analysis.hesitation_markers.map((marker, idx) => (
                        <span key={idx} className="emotion-tag">{marker}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Acoustic Features Section */}
        <div className="results-section">
          <div className="section-header">
            <div className="section-icon acoustic">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18V5l12-2v13"/>
                <circle cx="6" cy="18" r="3"/>
                <circle cx="18" cy="16" r="3"/>
              </svg>
            </div>
            <div className="section-title-group">
              <h2 className="section-title">Temel Akustik Ozellikler</h2>
              <p className="section-description">Ses dosyasindan cikarilan teknik parametreler</p>
            </div>
          </div>
          <div className="section-content">
            <div className="acoustic-grid">
              <div className="acoustic-item">
                <div className="acoustic-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12,6 12,12 16,14"/>
                  </svg>
                </div>
                <div className="acoustic-details">
                  <p className="acoustic-label">Sure</p>
                  <p className="acoustic-value">
                    {result.acoustic_features.duration.toFixed(2)}
                    <span className="acoustic-unit">saniye</span>
                  </p>
                </div>
              </div>
              <div className="acoustic-item">
                <div className="acoustic-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="11,5 6,9 2,9 2,15 6,15 11,19 11,5"/>
                    <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
                  </svg>
                </div>
                <div className="acoustic-details">
                  <p className="acoustic-label">Ortalama Enerji</p>
                  <p className="acoustic-value">{result.acoustic_features.energy.mean.toFixed(4)}</p>
                </div>
              </div>
              <div className="acoustic-item">
                <div className="acoustic-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M2 10v3"/>
                    <path d="M6 6v11"/>
                    <path d="M10 3v18"/>
                    <path d="M14 8v7"/>
                    <path d="M18 5v13"/>
                    <path d="M22 10v3"/>
                  </svg>
                </div>
                <div className="acoustic-details">
                  <p className="acoustic-label">Ortalama Pitch</p>
                  <p className="acoustic-value">
                    {result.acoustic_features.pitch.mean.toFixed(2)}
                    <span className="acoustic-unit">Hz</span>
                  </p>
                </div>
              </div>
              <div className="acoustic-item">
                <div className="acoustic-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 18V5l12-2v13"/>
                    <circle cx="6" cy="18" r="3"/>
                    <circle cx="18" cy="16" r="3"/>
                  </svg>
                </div>
                <div className="acoustic-details">
                  <p className="acoustic-label">Tempo</p>
                  <p className="acoustic-value">
                    {result.acoustic_features.tempo.toFixed(2)}
                    <span className="acoustic-unit">BPM</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Clinical Report Section */}
        {result.gemini_report ? (
          <div className="results-section" style={{gridColumn: 'span 2'}}>
            <div className="section-header">
              <div className="section-icon content">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                  <polyline points="14,2 14,8 20,8"/>
                  <line x1="16" x2="8" y1="13" y2="13"/>
                  <line x1="16" x2="8" y1="17" y2="17"/>
                </svg>
              </div>
              <div className="section-title-group">
                <h2 className="section-title">Klinik Degerlendirme ve Yorum</h2>
                <p className="section-description">AI tarafindan hazirlanan kapsamli analiz raporu</p>
              </div>
            </div>
            <div className="section-content">
              <div className="gemini-report-box">
                <div className="gemini-report-text">
                  <ReactMarkdown>
                    {result.gemini_report}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="results-section" style={{gridColumn: 'span 2'}}>
            <div className="section-header">
              <div className="section-icon content">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" x2="12" y1="8" y2="12"/>
                  <line x1="12" x2="12.01" y1="16" y2="16"/>
                </svg>
              </div>
              <div className="section-title-group">
                <h2 className="section-title">Klinik Degerlendirme ve Yorum</h2>
                <p className="section-description">AI raporu mevcut degil</p>
              </div>
            </div>
            <div className="section-content">
              <div style={{ padding: 'var(--spacing-lg)', textAlign: 'center', color: 'var(--text-muted)' }}>
                <p>AI raporu olusturulamadi. Bu durum API kotasi veya yapilandirma sorunundan kaynaklanabilir.</p>
                <p style={{ marginTop: 'var(--spacing-sm)', fontSize: '0.9rem' }}>Temel analiz sonuclari yukarida goruntulenmektedir.</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="results-actions">
        <Link to="/analyze" className="btn btn-primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" x2="12" y1="19" y2="22"/>
          </svg>
          Yeni Analiz
        </Link>
        <Link to="/" className="btn btn-secondary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
          Dashboard'a Don
        </Link>
      </div>
    </div>
  )
}
