import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Types
export interface AuthResponse {
  device_code: string
  user_code: string
  verification_uri: string
  expires_in: number
  interval: number
}

export interface AuthStatus {
  authenticated: boolean
  tenant_id?: string
  user_id?: string
  expires_at?: string
  error?: string
}

export interface PasswordLoginRequest {
  username: string
  password: string
  tenant_id: string
}

export interface ServicePrincipalLoginRequest {
  client_id: string
  client_secret: string
  tenant_id: string
}

export interface SecureScoreData {
  current_score: number
  max_score: number
  percentage: number
  control_scores: Array<{
    subscription_id: string
    score_name: string
    display_name: string
    current_score: number
    max_score: number
    percentage: number
  }>
}

export interface Recommendation {
  id: string
  name: string
  description: string
  severity: string
  category: string
  state: string
  affected_resources: number
}

export interface PublicResource {
  resource_id: string
  resource_name: string
  resource_type: string
  public_ip?: string
  ports: number[]
  protocols: string[]
  subscription_id: string
  resource_group: string
}

export interface NetworkSecurityGroup {
  id: string
  name: string
  location: string
  resource_group: string
  subscription_id: string
  rules: Array<{
    name: string
    priority: number
    direction: string
    access: string
    protocol: string
    source_port_range: string
    destination_port_range: string
    source_address_prefix: string
    destination_address_prefix: string
  }>
  risk_level: string
}

export interface UserInfo {
  id: string
  display_name: string
  user_principal_name: string
  mail?: string
  is_guest: boolean
  mfa_enabled: boolean
  sign_in_activity?: any
}

export interface RoleAssignment {
  principal_id: string
  principal_name: string
  principal_type: string
  role_definition_name: string
  scope: string
  subscription_id?: string
}

export interface PolicyAssignment {
  id: string
  name: string
  display_name: string
  policy_definition_id: string
  scope: string
  enforcement_mode: string
  compliance_state?: string
}

export interface ComplianceResult {
  policy_assignment_id: string
  policy_assignment_name: string
  resource_id: string
  compliance_state: string
  resource_type: string
  resource_location: string
}

export interface ScanResult {
  tenant_id: string
  scan_timestamp: string
  secure_score: SecureScoreData
  recommendations: Recommendation[]
  public_resources: PublicResource[]
  network_security_groups: NetworkSecurityGroup[]
  users: UserInfo[]
  role_assignments: RoleAssignment[]
  policy_assignments: PolicyAssignment[]
  compliance_results: ComplianceResult[]
}

export interface Subscription {
  subscription_id: string
  display_name: string
  state: string
  tenant_id: string
}

// API functions
export const authApi = {
  initiateLogin: (): Promise<AuthResponse> => api.post('/login').then(res => res.data),

  loginWithPassword: (credentials: PasswordLoginRequest): Promise<AuthStatus> =>
    api.post('/login/password', credentials).then(res => res.data),

  loginWithServicePrincipal: (credentials: ServicePrincipalLoginRequest): Promise<AuthStatus> =>
    api.post('/login/service-principal', credentials).then(res => res.data),

  loginWithCli: (): Promise<AuthStatus> => api.post('/login/cli').then(res => res.data),

  completeAuthentication: (): Promise<AuthStatus> =>
    api.post('/auth/complete').then(res => res.data),

  getStatus: (): Promise<AuthStatus> => api.get('/auth/status').then(res => res.data),
}

export const scanApi = {
  runFullScan: (): Promise<ScanResult> => api.post('/scan').then(res => res.data),

  getLatestScan: (): Promise<ScanResult | null> => api.get('/scan/latest').then(res => res.data),

  getSubscriptions: (): Promise<Subscription[]> => api.get('/subscriptions').then(res => res.data),
}

export const moduleApi = {
  getSecureScore: (): Promise<SecureScoreData> => api.get('/secure_score').then(res => res.data),

  getRecommendations: (): Promise<Recommendation[]> =>
    api.get('/recommendations').then(res => res.data),

  getExposure: (): Promise<PublicResource[]> => api.get('/exposure').then(res => res.data),

  getNSGs: (): Promise<NetworkSecurityGroup[]> => api.get('/nsgs').then(res => res.data),

  getIdentity: (): Promise<UserInfo[]> => api.get('/identity').then(res => res.data),

  getRoles: (): Promise<RoleAssignment[]> => api.get('/roles').then(res => res.data),

  getPolicy: (): Promise<PolicyAssignment[]> => api.get('/policy').then(res => res.data),

  getCompliance: (): Promise<ComplianceResult[]> => api.get('/compliance').then(res => res.data),
}

export const reportApi = {
  generateReport: (format: 'markdown' | 'pdf') => {
    return api
      .post(
        '/report',
        { format },
        {
          responseType: format === 'pdf' ? 'blob' : 'blob',
        }
      )
      .then(res => {
        const blob = new Blob([res.data], {
          type: format === 'pdf' ? 'application/pdf' : 'text/markdown',
        })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `azure_recon_report.${format === 'pdf' ? 'pdf' : 'md'}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      })
  },

  listReports: () => api.get('/reports').then(res => res.data),
}
