import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { getCurrentUser, UserResponse } from '../api/auth'

interface AuthContextType {
    user: UserResponse | null
    token: string | null
    isAuthenticated: boolean
    isLoading: boolean
    login: (token: string) => void
    logout: () => void
    refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<UserResponse | null>(null)
    const [token, setToken] = useState<string | null>(null)
    const [isLoading, setIsLoading] = useState(true)

    const refreshUser = async () => {
        const storedToken = localStorage.getItem('token')
        if (storedToken) {
            try {
                const userData = await getCurrentUser()
                setUser(userData)
                setToken(storedToken)
            } catch (error) {
                // Token geçersiz
                localStorage.removeItem('token')
                localStorage.removeItem('user')
                setUser(null)
                setToken(null)
            }
        }
        setIsLoading(false)
    }

    useEffect(() => {
        refreshUser()
    }, [])

    const login = (newToken: string) => {
        localStorage.setItem('token', newToken)
        setToken(newToken)
        refreshUser()
    }

    const logout = () => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        setUser(null)
        setToken(null)
        window.location.href = '/login'
    }

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                isAuthenticated: !!token && !!user,
                isLoading,
                login,
                logout,
                refreshUser,
            }}
        >
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
