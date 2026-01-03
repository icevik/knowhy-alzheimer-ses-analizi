import { useEffect, useState } from 'react'
import './AnalysisTimeline.css'

interface Step {
  step: number
  title: string
  description: string
}

interface ProgressData {
  current_step: number
  total_steps: number
  message: string
  status: string
  steps: Step[]
}

interface AnalysisTimelineProps {
  progressId: string | null
  isAnalyzing: boolean
  onComplete?: () => void
}

const DEFAULT_STEPS: Step[] = [
  { step: 1, title: "Dosya Yükleme", description: "Ses dosyası yükleniyor..." },
  { step: 2, title: "Akustik Analiz", description: "Temel akustik özellikler çıkarılıyor..." },
  { step: 3, title: "Gelişmiş Akustik", description: "Jitter, shimmer, formant analizi..." },
  { step: 4, title: "Transkripsiyon", description: "Konuşma metne dönüştürülüyor (Whisper)..." },
  { step: 5, title: "Dilbilimsel Analiz", description: "Metin analizi yapılıyor..." },
  { step: 6, title: "Duygu Analizi", description: "Duygu ve içerik analizi..." },
  { step: 7, title: "Klinik Rapor", description: "AI klinik raporu oluşturuluyor..." },
  { step: 8, title: "PDF Oluşturma", description: "PDF rapor hazırlanıyor..." },
  { step: 9, title: "Kayıt", description: "Veritabanına kaydediliyor..." },
]

export default function AnalysisTimeline({ progressId, isAnalyzing, onComplete }: AnalysisTimelineProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null)
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    if (!progressId || !isAnalyzing) {
      setCurrentStep(0)
      setProgress(null)
      return
    }

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const eventSource = new EventSource(`${API_URL}/api/analyze/progress/${progressId}/stream`)

    eventSource.onmessage = (event) => {
      try {
        const data: ProgressData = JSON.parse(event.data)
        setProgress(data)
        setCurrentStep(data.current_step)

        if (data.status === 'completed') {
          eventSource.close()
          onComplete?.()
        } else if (data.status === 'error') {
          eventSource.close()
        }
      } catch (e) {
        console.error('Progress parse error:', e)
      }
    }

    eventSource.onerror = () => {
      // Connection error - might be normal when analysis completes
      eventSource.close()
    }

    return () => {
      eventSource.close()
    }
  }, [progressId, isAnalyzing, onComplete])

  // Polling fallback - daha sık güncelleme
  useEffect(() => {
    if (!progressId || !isAnalyzing) return

    const pollProgress = async () => {
      try {
        const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
        const response = await fetch(`${API_URL}/api/analyze/progress/${progressId}`)
        if (response.ok) {
          const data = await response.json()
          if (data.current_step > 0 && data.current_step !== currentStep) {
            console.log('[Timeline] Progress güncellendi:', data.current_step)
            setCurrentStep(data.current_step)
            setProgress(data)
          }
        }
      } catch (e) {
        // Ignore polling errors
      }
    }

    // İlk poll hemen yap
    pollProgress()

    // Her 500ms'de bir poll yap (daha hızlı güncelleme)
    const interval = setInterval(pollProgress, 500)
    return () => clearInterval(interval)
  }, [progressId, isAnalyzing, currentStep])

  const steps = progress?.steps || DEFAULT_STEPS

  const getStepStatus = (stepNumber: number): 'completed' | 'active' | 'pending' => {
    if (stepNumber < currentStep) return 'completed'
    if (stepNumber === currentStep) return 'active'
    return 'pending'
  }

  if (!isAnalyzing) {
    return null
  }

  return (
    <div className="analysis-timeline">
      <div className="timeline-header">
        <h3>Analiz İlerlemesi (Ekran donmuş gibi görünebilir. Lütfen bekleyiniz)</h3>
        <span className="step-counter">Adım {currentStep} / {steps.length}</span>
      </div>

      <div className="timeline-container">
        {steps.map((step, index) => {
          const status = getStepStatus(step.step)
          return (
            <div key={step.step} className={`timeline-step ${status}`}>
              <div className="step-indicator">
                <div className="step-circle">
                  {status === 'completed' ? (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  ) : status === 'active' ? (
                    <div className="step-spinner" />
                  ) : (
                    <span>{step.step}</span>
                  )}
                </div>
                {index < steps.length - 1 && <div className="step-line" />}
              </div>

              <div className="step-content">
                <div className="step-title">{step.title}</div>
                <div className="step-description">
                  {status === 'active' && progress?.message
                    ? progress.message
                    : step.description}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="timeline-footer">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${(currentStep / steps.length) * 100}%` }}
          />
        </div>
        <p className="progress-text">
          {progress?.status === 'completed'
            ? 'Analiz tamamlandı!'
            : 'Analiz devam ediyor, lütfen bekleyin...'}
        </p>
      </div>
    </div>
  )
}

