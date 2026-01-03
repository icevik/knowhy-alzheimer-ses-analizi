import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login, verifyLogin } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import './LoginPage.css'

type Step = 'credentials' | 'verification'

export default function LoginPage() {
    const navigate = useNavigate()
    const { login: authLogin } = useAuth()

    const [step, setStep] = useState<Step>('credentials')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [verificationCode, setVerificationCode] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState('')
    const [message, setMessage] = useState('')

    const handleCredentialsSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setIsLoading(true)

        try {
            const response = await login(email, password)
            setMessage(response.message)
            setStep('verification')
        } catch (err: any) {
            const detail = err.response?.data?.detail || 'Giriş başarısız'
            setError(detail)
        } finally {
            setIsLoading(false)
        }
    }

    const handleVerificationSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setIsLoading(true)

        try {
            const response = await verifyLogin(email, verificationCode)
            authLogin(response.access_token)
            navigate('/')
        } catch (err: any) {
            const detail = err.response?.data?.detail || 'Doğrulama başarısız'
            setError(detail)
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-container">
                <div className="auth-header">
                    <img src="/logo.png" alt="KNOWHY Logo" className="auth-logo" />
                    <h1>KNOWHY Alzheimer Analiz</h1>
                    <p>Hesabınıza giriş yapın</p>
                </div>

                {step === 'credentials' ? (
                    <form onSubmit={handleCredentialsSubmit} className="auth-form">
                        <div className="form-group">
                            <label htmlFor="email">Email</label>
                            <input
                                type="email"
                                id="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="ornek@email.com"
                                required
                                disabled={isLoading}
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="password">Şifre</label>
                            <input
                                type="password"
                                id="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                disabled={isLoading}
                            />
                        </div>

                        {error && <div className="auth-error">{error}</div>}

                        <button type="submit" className="auth-button" disabled={isLoading}>
                            {isLoading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
                        </button>
                    </form>
                ) : (
                    <form onSubmit={handleVerificationSubmit} className="auth-form">
                        <div className="verification-info">
                            <span className="verification-icon">📧</span>
                            <p>{message}</p>
                            <p className="verification-email">{email}</p>
                        </div>

                        <div className="form-group">
                            <label htmlFor="code">Doğrulama Kodu</label>
                            <input
                                type="text"
                                id="code"
                                value={verificationCode}
                                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                placeholder="6 haneli kod"
                                maxLength={6}
                                required
                                disabled={isLoading}
                                className="code-input"
                            />
                        </div>

                        {error && <div className="auth-error">{error}</div>}

                        <button type="submit" className="auth-button" disabled={isLoading || verificationCode.length !== 6}>
                            {isLoading ? 'Doğrulanıyor...' : 'Doğrula ve Giriş Yap'}
                        </button>

                        <button
                            type="button"
                            className="auth-link-button"
                            onClick={() => {
                                setStep('credentials')
                                setVerificationCode('')
                                setError('')
                            }}
                        >
                            ← Geri Dön
                        </button>
                    </form>
                )}

                <div className="auth-footer">
                    <p>
                        Hesabınız yok mu?{' '}
                        <Link to="/register" className="auth-link">
                            Kayıt Ol
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    )
}
