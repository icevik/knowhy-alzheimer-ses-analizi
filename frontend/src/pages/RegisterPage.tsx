import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register, verifyRegister } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import './LoginPage.css'

type Step = 'register' | 'verification'

export default function RegisterPage() {
    const navigate = useNavigate()
    const { login: authLogin } = useAuth()

    const [step, setStep] = useState<Step>('register')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [verificationCode, setVerificationCode] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState('')
    const [message, setMessage] = useState('')

    const handleRegisterSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')

        // Şifre kontrolü
        if (password !== confirmPassword) {
            setError('Şifreler eşleşmiyor')
            return
        }

        if (password.length < 8) {
            setError('Şifre en az 8 karakter olmalıdır')
            return
        }

        setIsLoading(true)

        try {
            const response = await register(email, password)
            setMessage(response.message)
            setStep('verification')
        } catch (err: any) {
            const detail = err.response?.data?.detail || 'Kayıt başarısız'
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
            const response = await verifyRegister(email, verificationCode)
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
                    <p>Yeni hesap oluşturun</p>
                </div>

                {step === 'register' ? (
                    <form onSubmit={handleRegisterSubmit} className="auth-form">
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
                                minLength={8}
                            />
                            <span className="password-requirements">En az 8 karakter</span>
                        </div>

                        <div className="form-group">
                            <label htmlFor="confirmPassword">Şifre Tekrar</label>
                            <input
                                type="password"
                                id="confirmPassword"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                disabled={isLoading}
                            />
                        </div>

                        {error && <div className="auth-error">{error}</div>}

                        <button type="submit" className="auth-button" disabled={isLoading}>
                            {isLoading ? 'Kayıt yapılıyor...' : 'Kayıt Ol'}
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
                                setStep('register')
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
                        Zaten hesabınız var mı?{' '}
                        <Link to="/login" className="auth-link">
                            Giriş Yap
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    )
}
