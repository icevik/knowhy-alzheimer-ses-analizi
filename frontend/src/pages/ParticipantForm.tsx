import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createParticipant, ParticipantCreate } from '../api/participants'
import './ParticipantForm.css'

export default function ParticipantForm() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState<ParticipantCreate>({
    name: '',
    age: 55,
    gender: '',
    group_type: 'control',
    mmse_score: null,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const participant = await createParticipant(formData)
      navigate(`/analyze?participant_id=${participant.id}`)
    } catch (error: any) {
      alert('Hata: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="participant-form-page">
      <div className="form-header">
        <h1 className="form-title">Yeni Katilimci</h1>
        <p className="form-subtitle">Katilimci bilgilerini girerek yeni bir kayit olusturun</p>
      </div>

      <form onSubmit={handleSubmit} className="form-card">
        {/* Kisisel Bilgiler */}
        <div className="form-section">
          <h3 className="form-section-title">Kisisel Bilgiler</h3>

          <div className="form-group">
            <label className="form-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
              Ad Soyad
              <span className="required-mark">*</span>
            </label>
            <input
              type="text"
              className="form-input"
              placeholder="Katilimcinin tam adi"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                  <line x1="16" x2="16" y1="2" y2="6" />
                  <line x1="8" x2="8" y1="2" y2="6" />
                  <line x1="3" x2="21" y1="10" y2="10" />
                </svg>
                Yas
                <span className="required-mark">*</span>
              </label>
              <input
                type="number"
                className="form-input"
                required
                value={formData.age}
                onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) })}
              />
              <p className="form-help">Katılımcı yaşı</p>
            </div>

            <div className="form-group">
              <label className="form-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 8v8" />
                  <path d="M8 12h8" />
                </svg>
                Cinsiyet
                <span className="required-mark">*</span>
              </label>
              <div className="gender-selector">
                <label className="gender-option">
                  <input
                    type="radio"
                    name="gender"
                    value="erkek"
                    checked={formData.gender === 'erkek'}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                    required
                  />
                  <span className="gender-option-label">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="10" cy="14" r="5" />
                      <path d="M19 5l-5.4 5.4" />
                      <path d="M15 5h4v4" />
                    </svg>
                    Erkek
                  </span>
                </label>
                <label className="gender-option">
                  <input
                    type="radio"
                    name="gender"
                    value="kadin"
                    checked={formData.gender === 'kadin'}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                  />
                  <span className="gender-option-label">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="8" r="5" />
                      <path d="M12 13v9" />
                      <path d="M9 18h6" />
                    </svg>
                    Kadin
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Klinik Bilgiler */}
        <div className="form-section">
          <h3 className="form-section-title">Klinik Bilgiler</h3>

          <div className="form-group">
            <label className="form-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
              Grup Tipi
              <span className="required-mark">*</span>
            </label>
            <div className="group-selector">
              <label className="group-option">
                <input
                  type="radio"
                  name="group_type"
                  value="alzheimer"
                  checked={formData.group_type === 'alzheimer'}
                  onChange={(e) => setFormData({ ...formData, group_type: e.target.value as any })}
                />
                <span className="group-option-label">
                  <span className="group-dot alzheimer"></span>
                  <span className="group-option-name">Alzheimer</span>
                  <span className="group-option-desc">Tani konulmus</span>
                </span>
              </label>
              <label className="group-option">
                <input
                  type="radio"
                  name="group_type"
                  value="mci"
                  checked={formData.group_type === 'mci'}
                  onChange={(e) => setFormData({ ...formData, group_type: e.target.value as any })}
                />
                <span className="group-option-label">
                  <span className="group-dot mci"></span>
                  <span className="group-option-name">MCI</span>
                  <span className="group-option-desc">Hafif bilissel bozukluk</span>
                </span>
              </label>
              <label className="group-option">
                <input
                  type="radio"
                  name="group_type"
                  value="control"
                  checked={formData.group_type === 'control'}
                  onChange={(e) => setFormData({ ...formData, group_type: e.target.value as any })}
                />
                <span className="group-option-label">
                  <span className="group-dot control"></span>
                  <span className="group-option-name">Kontrol</span>
                  <span className="group-option-desc">Saglikli birey</span>
                </span>
              </label>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
              MMSE Skoru
            </label>
            <input
              type="number"
              className="form-input"
              placeholder="0-30 arasi (opsiyonel)"
              min="0"
              max="30"
              value={formData.mmse_score || ''}
              onChange={(e) => setFormData({
                ...formData,
                mmse_score: e.target.value ? parseInt(e.target.value) : null
              })}
            />
            <p className="form-help">Mini Mental State Examination skoru (0-30)</p>
          </div>
        </div>

        <div className="submit-section">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/')}
          >
            Iptal
          </button>
          <button
            type="submit"
            disabled={loading}
            className={`btn btn-primary ${loading ? 'btn-loading' : ''}`}
          >
            {!loading && (
              <>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                  <polyline points="17,21 17,13 7,13 7,21" />
                  <polyline points="7,3 7,8 15,8" />
                </svg>
                Kaydet ve Devam Et
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
