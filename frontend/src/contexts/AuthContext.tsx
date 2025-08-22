import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi, PasswordLoginRequest, ServicePrincipalLoginRequest } from '../services/api'

interface AuthStatus {
  authenticated: boolean
  tenant_id?: string
  user_id?: string
  expires_at?: string
  error?: string
}

interface AuthContextType {
  isAuthenticated: boolean
  authStatus: AuthStatus | null
  loading: boolean
  login: () => Promise<void>
  loginWithPassword: (credentials: PasswordLoginRequest) => Promise<void>
  loginWithServicePrincipal: (credentials: ServicePrincipalLoginRequest) => Promise<void>
  loginWithCli: () => Promise<void>
  checkAuthStatus: () => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null)
  const [loading, setLoading] = useState(true)

  const checkAuthStatus = async () => {
    try {
      const status = await authApi.getStatus()
      setAuthStatus(status)
    } catch (error) {
      console.error('Auth check failed:', error)
      setAuthStatus({ authenticated: false })
    } finally {
      setLoading(false)
    }
  }

  const login = async () => {
    try {
      setLoading(true)

      // Initiate device code flow
      const authResponse = await authApi.initiateLogin()

      // Show device code to user
      const userConfirmed = window.confirm(
        `Please visit ${authResponse.verification_uri} and enter the code: ${authResponse.user_code}\n\nClick OK when you've completed the authentication process.`
      )

      if (!userConfirmed) {
        setLoading(false)
        return
      }

      // Complete authentication
      const status = await authApi.completeAuthentication()
      setAuthStatus(status)

      if (status.authenticated) {
        window.location.href = '/dashboard'
      } else {
        alert('Authentication failed. Please try again.')
      }
    } catch (error) {
      console.error('Login failed:', error)
      alert('Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const loginWithPassword = async (credentials: PasswordLoginRequest) => {
    try {
      setLoading(true)
      const status = await authApi.loginWithPassword(credentials)
      setAuthStatus(status)

      if (status.authenticated) {
        window.location.href = '/dashboard'
      } else {
        throw new Error(status.error || 'Authentication failed')
      }
    } catch (error) {
      console.error('Password login failed:', error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const loginWithServicePrincipal = async (credentials: ServicePrincipalLoginRequest) => {
    try {
      setLoading(true)
      const status = await authApi.loginWithServicePrincipal(credentials)
      setAuthStatus(status)

      if (status.authenticated) {
        window.location.href = '/dashboard'
      } else {
        throw new Error(status.error || 'Service principal authentication failed')
      }
    } catch (error) {
      console.error('Service principal login failed:', error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const loginWithCli = async () => {
    try {
      setLoading(true)
      const status = await authApi.loginWithCli()
      setAuthStatus(status)

      if (status.authenticated) {
        window.location.href = '/dashboard'
      } else {
        throw new Error(status.error || 'Azure CLI authentication failed')
      }
    } catch (error) {
      console.error('CLI login failed:', error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    setAuthStatus({ authenticated: false })
    window.location.href = '/login'
  }

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const value: AuthContextType = {
    isAuthenticated: authStatus?.authenticated || false,
    authStatus,
    loading,
    login,
    loginWithPassword,
    loginWithServicePrincipal,
    loginWithCli,
    checkAuthStatus,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
