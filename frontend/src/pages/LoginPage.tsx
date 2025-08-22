import React, { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Shield, User, Lock, Globe, Key, QrCode, Server, Terminal } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { LoadingSpinner } from '../components/LoadingSpinner'

const LoginPage: React.FC = () => {
  const {
    isAuthenticated,
    loading,
    login,
    loginWithPassword,
    loginWithServicePrincipal,
    loginWithCli,
  } = useAuth()
  const [authMethod, setAuthMethod] = useState<'device' | 'password' | 'service_principal' | 'cli'>(
    'cli'
  )
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    tenant_id: '',
    client_id: '',
    client_secret: '',
  })
  const [formLoading, setFormLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isAuthenticated) {
      // Redirect if already authenticated
    }
  }, [isAuthenticated])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  const handleLogin = async () => {
    try {
      setError('')
      await login()
    } catch (error) {
      console.error('Login error:', error)
      setError('Device code login failed. Please try again.')
    }
  }

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.username || !formData.password || !formData.tenant_id) {
      setError('Please fill in all fields')
      return
    }

    try {
      setError('')
      setFormLoading(true)
      await loginWithPassword({
        username: formData.username,
        password: formData.password,
        tenant_id: formData.tenant_id,
      })
    } catch (error: any) {
      console.error('Password login error:', error)
      setError(error?.response?.data?.detail || error?.message || 'Password login failed')
    } finally {
      setFormLoading(false)
    }
  }

  const handleServicePrincipalLogin = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.client_id || !formData.client_secret || !formData.tenant_id) {
      setError('Please fill in all fields')
      return
    }

    try {
      setError('')
      setFormLoading(true)
      await loginWithServicePrincipal({
        client_id: formData.client_id,
        client_secret: formData.client_secret,
        tenant_id: formData.tenant_id,
      })
    } catch (error: any) {
      console.error('Service principal login error:', error)
      setError(error?.response?.data?.detail || error?.message || 'Service principal login failed')
    } finally {
      setFormLoading(false)
    }
  }

  const handleCliLogin = async () => {
    try {
      setError('')
      setFormLoading(true)
      await loginWithCli()
    } catch (error: any) {
      console.error('CLI login error:', error)
      setError(error?.response?.data?.detail || error?.message || 'Azure CLI login failed')
    } finally {
      setFormLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-primary-100">
            <Shield className="h-8 w-8 text-primary-600" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">Azure Recon</h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Security Assessment and Posture Analysis Tool
          </p>
        </div>

        <div className="bg-white shadow rounded-lg p-8">
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Connect to Azure</h3>
              <p className="text-sm text-gray-600 mb-6">
                Choose your authentication method to begin security assessment
              </p>
            </div>

            {/* Authentication method selector */}
            <div className="grid grid-cols-4 rounded-md bg-gray-100 p-1 gap-1">
              <button
                onClick={() => setAuthMethod('device')}
                className={`flex items-center justify-center space-x-1 px-2 py-2 text-xs font-medium rounded-sm transition-colors ${
                  authMethod === 'device'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <QrCode className="h-3 w-3" />
                <span>Device</span>
              </button>
              <button
                onClick={() => setAuthMethod('password')}
                className={`flex items-center justify-center space-x-1 px-2 py-2 text-xs font-medium rounded-sm transition-colors ${
                  authMethod === 'password'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Key className="h-3 w-3" />
                <span>Password</span>
              </button>
              <button
                onClick={() => setAuthMethod('service_principal')}
                className={`flex items-center justify-center space-x-1 px-2 py-2 text-xs font-medium rounded-sm transition-colors ${
                  authMethod === 'service_principal'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Server className="h-3 w-3" />
                <span>App Registration</span>
              </button>
              <button
                onClick={() => setAuthMethod('cli')}
                className={`flex items-center justify-center space-x-1 px-2 py-2 text-xs font-medium rounded-sm transition-colors ${
                  authMethod === 'cli'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Terminal className="h-3 w-3" />
                <span>Azure CLI</span>
              </button>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <div className="text-sm text-red-700">{error}</div>
              </div>
            )}

            {authMethod === 'device' && (
              <div className="space-y-4">
                <div className="space-y-4">
                  <div className="flex items-center space-x-3 text-sm text-gray-600">
                    <User className="h-5 w-5 text-gray-400" />
                    <span>Uses Azure Device Code Flow for secure authentication</span>
                  </div>
                  <div className="flex items-center space-x-3 text-sm text-gray-600">
                    <Lock className="h-5 w-5 text-gray-400" />
                    <span>Requires Reader-level access to your Azure tenant</span>
                  </div>
                  <div className="flex items-center space-x-3 text-sm text-gray-600">
                    <Globe className="h-5 w-5 text-gray-400" />
                    <span>Read-only analysis - no changes will be made</span>
                  </div>
                </div>

                <div className="pt-4">
                  <button
                    onClick={handleLogin}
                    disabled={loading}
                    className="w-full btn-primary flex justify-center items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <>
                        <LoadingSpinner size="sm" />
                        <span>Authenticating...</span>
                      </>
                    ) : (
                      <>
                        <QrCode className="h-5 w-5" />
                        <span>Sign in with Device Code</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {authMethod === 'password' && (
              <form onSubmit={handlePasswordLogin} className="space-y-4">
                <div>
                  <label
                    htmlFor="username"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Username
                  </label>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    required
                    value={formData.username}
                    onChange={handleInputChange}
                    placeholder="user@company.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div>
                  <label
                    htmlFor="password"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Password
                  </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    value={formData.password}
                    onChange={handleInputChange}
                    placeholder="Your password"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div>
                  <label
                    htmlFor="tenant_id"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Tenant ID
                  </label>
                  <input
                    id="tenant_id"
                    name="tenant_id"
                    type="text"
                    required
                    value={formData.tenant_id}
                    onChange={handleInputChange}
                    placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={formLoading || loading}
                    className="w-full btn-primary flex justify-center items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {formLoading ? (
                      <>
                        <LoadingSpinner size="sm" />
                        <span>Authenticating...</span>
                      </>
                    ) : (
                      <>
                        <Key className="h-5 w-5" />
                        <span>Sign in with Password</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}

            {authMethod === 'service_principal' && (
              <form onSubmit={handleServicePrincipalLogin} className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4">
                  <div className="text-sm text-blue-800">
                    <strong>App Registration (Service Principal)</strong> - Bypasses most
                    Conditional Access policies
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="client_id"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Application (Client) ID
                  </label>
                  <input
                    id="client_id"
                    name="client_id"
                    type="text"
                    required
                    value={formData.client_id}
                    onChange={handleInputChange}
                    placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div>
                  <label
                    htmlFor="client_secret"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Client Secret
                  </label>
                  <input
                    id="client_secret"
                    name="client_secret"
                    type="password"
                    required
                    value={formData.client_secret}
                    onChange={handleInputChange}
                    placeholder="Your client secret"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div>
                  <label
                    htmlFor="tenant_id_sp"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Tenant ID
                  </label>
                  <input
                    id="tenant_id_sp"
                    name="tenant_id"
                    type="text"
                    required
                    value={formData.tenant_id}
                    onChange={handleInputChange}
                    placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={formLoading || loading}
                    className="w-full btn-primary flex justify-center items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {formLoading ? (
                      <>
                        <LoadingSpinner size="sm" />
                        <span>Authenticating...</span>
                      </>
                    ) : (
                      <>
                        <Server className="h-5 w-5" />
                        <span>Sign in with App Registration</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}

            {authMethod === 'cli' && (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-md p-3 mb-4">
                  <div className="text-sm text-green-800">
                    <strong>Azure CLI</strong> - Uses your existing <code>az login</code> session
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center space-x-3 text-sm text-gray-600">
                    <Terminal className="h-5 w-5 text-gray-400" />
                    <span>Leverages your existing Azure CLI authentication</span>
                  </div>
                  <div className="flex items-center space-x-3 text-sm text-gray-600">
                    <Lock className="h-5 w-5 text-gray-400" />
                    <span>No additional credentials needed</span>
                  </div>
                  <div className="flex items-center space-x-3 text-sm text-gray-600">
                    <Globe className="h-5 w-5 text-gray-400" />
                    <span>Uses the same permissions as your CLI session</span>
                  </div>
                </div>

                <div className="pt-4">
                  <button
                    onClick={handleCliLogin}
                    disabled={formLoading || loading}
                    className="w-full btn-primary flex justify-center items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {formLoading ? (
                      <>
                        <LoadingSpinner size="sm" />
                        <span>Authenticating...</span>
                      </>
                    ) : (
                      <>
                        <Terminal className="h-5 w-5" />
                        <span>Use Azure CLI Session</span>
                      </>
                    )}
                  </button>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                  <div className="text-sm text-blue-800">
                    <strong>Prerequisites:</strong> Make sure you're logged in with{' '}
                    <code>az login</code> first
                  </div>
                </div>
              </div>
            )}

            <div className="text-xs text-gray-500 text-center mt-4">
              <p>
                By signing in, you agree to allow this application to read your Azure configuration
                for security assessment purposes only.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm">
            <h4 className="font-medium text-blue-900 mb-2">What this tool does:</h4>
            <ul className="space-y-1 text-blue-800">
              <li>• Analyzes your Azure security posture</li>
              <li>• Reviews Microsoft Defender recommendations</li>
              <li>• Identifies publicly exposed resources</li>
              <li>• Audits identity and access configurations</li>
              <li>• Generates comprehensive security reports</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
