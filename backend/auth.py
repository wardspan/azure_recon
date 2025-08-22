import os
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from azure.identity import DeviceCodeCredential, UsernamePasswordCredential, ClientSecretCredential, AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.subscription import SubscriptionClient
from msgraph import GraphServiceClient
from models import AuthResponse, AuthStatus, Subscription
import logging

logger = logging.getLogger(__name__)

class AzureAuth:
    def __init__(self):
        self.credential: Optional[DeviceCodeCredential | UsernamePasswordCredential | ClientSecretCredential | AzureCliCredential] = None
        self.tenant_id: Optional[str] = None
        self.authenticated = False
        self.expires_at: Optional[datetime] = None
        self.graph_client: Optional[GraphServiceClient] = None
        self.auth_method: Optional[str] = None
        
    def device_code_callback(self, verification_uri: str, user_code: str, expires_in: int):
        """Callback for device code flow"""
        logger.info(f"Device code: {user_code}")
        logger.info(f"Verification URI: {verification_uri}")
        logger.info(f"Expires in: {expires_in} seconds")
    
    async def initiate_device_code_flow(self) -> AuthResponse:
        """Start the device code authentication flow"""
        try:
            self.credential = DeviceCodeCredential(
                client_id=os.getenv("AZURE_CLIENT_ID", "04b07795-8ddb-461a-bbee-02f9e1bf7b46"),  # Azure CLI client ID
                tenant_id=os.getenv("AZURE_TENANT_ID"),
                device_code_callback=self.device_code_callback,
                timeout=300
            )
            
            # Get the device code information
            # Note: This is a simplified approach. In a real implementation,
            # you might need to extract this information from the credential setup
            return AuthResponse(
                device_code="temp_device_code",
                user_code="temp_user_code", 
                verification_uri="https://microsoft.com/devicelogin",
                expires_in=900,
                interval=5
            )
        except Exception as e:
            logger.error(f"Error initiating device code flow: {str(e)}")
            raise
    
    async def authenticate_with_password(self, username: str, password: str, tenant_id: str) -> AuthStatus:
        """Authenticate using username and password"""
        try:
            self.credential = UsernamePasswordCredential(
                client_id=os.getenv("AZURE_CLIENT_ID", "04b07795-8ddb-461a-bbee-02f9e1bf7b46"),  # Azure CLI client ID
                username=username,
                password=password,
                tenant_id=tenant_id
            )
            self.auth_method = "password"
            self.tenant_id = tenant_id
            
            # Test authentication by getting a token
            token = self.credential.get_token("https://management.azure.com/.default")
            
            if token:
                self.authenticated = True
                self.expires_at = datetime.now() + timedelta(seconds=token.expires_on - int(datetime.now().timestamp()))
                
                # Initialize Graph client
                self.graph_client = GraphServiceClient(
                    credentials=self.credential,
                    scopes=["https://graph.microsoft.com/.default"]
                )
                
                return AuthStatus(
                    authenticated=True,
                    tenant_id=self.tenant_id,
                    expires_at=self.expires_at
                )
            else:
                return AuthStatus(authenticated=False)
                
        except Exception as e:
            logger.error(f"Username/password authentication error: {str(e)}")
            return AuthStatus(authenticated=False, error=str(e))
    
    async def authenticate_with_service_principal(self, client_id: str, client_secret: str, tenant_id: str) -> AuthStatus:
        """Authenticate using service principal (App ID + Secret)"""
        try:
            self.credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            self.auth_method = "service_principal"
            self.tenant_id = tenant_id
            
            # Test authentication by getting a token
            token = self.credential.get_token("https://management.azure.com/.default")
            
            if token:
                self.authenticated = True
                self.expires_at = datetime.now() + timedelta(seconds=token.expires_on - int(datetime.now().timestamp()))
                
                # Initialize Graph client
                self.graph_client = GraphServiceClient(
                    credentials=self.credential,
                    scopes=["https://graph.microsoft.com/.default"]
                )
                
                return AuthStatus(
                    authenticated=True,
                    tenant_id=self.tenant_id,
                    expires_at=self.expires_at
                )
            else:
                return AuthStatus(authenticated=False)
                
        except Exception as e:
            logger.error(f"Service principal authentication error: {str(e)}")
            return AuthStatus(authenticated=False, error=str(e))
    
    async def authenticate_with_cli(self) -> AuthStatus:
        """Authenticate using existing Azure CLI session"""
        try:
            self.credential = AzureCliCredential()
            self.auth_method = "cli"
            
            # Test authentication by getting a token
            token = self.credential.get_token("https://management.azure.com/.default")
            
            if token:
                self.authenticated = True
                self.expires_at = datetime.now() + timedelta(seconds=token.expires_on - int(datetime.now().timestamp()))
                
                # Initialize Graph client
                self.graph_client = GraphServiceClient(
                    credentials=self.credential,
                    scopes=["https://graph.microsoft.com/.default"]
                )
                
                # Get tenant information from CLI context
                try:
                    import subprocess
                    import json
                    result = subprocess.run(['az', 'account', 'show'], capture_output=True, text=True, check=True)
                    account_info = json.loads(result.stdout)
                    self.tenant_id = account_info.get('tenantId')
                except Exception as e:
                    logger.warning(f"Could not get tenant ID from CLI: {str(e)}")
                    # Don't try Graph API for CLI auth as it may not have the right permissions
                    pass
                
                return AuthStatus(
                    authenticated=True,
                    tenant_id=self.tenant_id,
                    expires_at=self.expires_at
                )
            else:
                return AuthStatus(authenticated=False, error="Failed to obtain token from Azure CLI")
                
        except Exception as e:
            logger.error(f"Azure CLI authentication error: {str(e)}")
            return AuthStatus(authenticated=False, error=f"Azure CLI authentication failed: {str(e)}. Make sure you're logged in with 'az login'")
    
    async def complete_authentication(self) -> AuthStatus:
        """Complete the authentication process"""
        try:
            if not self.credential:
                raise ValueError("Authentication not initiated")
            
            # Get a token to test authentication
            token = self.credential.get_token("https://management.azure.com/.default")
            
            if token:
                self.authenticated = True
                self.expires_at = datetime.now() + timedelta(seconds=token.expires_on - int(datetime.now().timestamp()))
                self.auth_method = "device_code"
                
                # Initialize Graph client
                self.graph_client = GraphServiceClient(
                    credentials=self.credential,
                    scopes=["https://graph.microsoft.com/.default"]
                )
                
                # Get tenant information (only for device code flow, as password flow already has tenant_id)
                if not self.tenant_id:
                    try:
                        organizations = await self.graph_client.organization.get()
                        if organizations and hasattr(organizations, 'value') and organizations.value:
                            self.tenant_id = organizations.value[0].id
                    except Exception as e:
                        logger.warning(f"Could not get tenant ID: {str(e)}")
                
                return AuthStatus(
                    authenticated=True,
                    tenant_id=self.tenant_id,
                    expires_at=self.expires_at
                )
            else:
                return AuthStatus(authenticated=False)
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return AuthStatus(authenticated=False)
    
    async def get_subscriptions(self) -> list[Subscription]:
        """Get all accessible subscriptions"""
        if not self.authenticated or not self.credential:
            raise ValueError("Not authenticated")
        
        subscriptions = []
        try:
            subscription_client = SubscriptionClient(credential=self.credential)
            for sub in subscription_client.subscriptions.list():
                subscriptions.append(Subscription(
                    subscription_id=sub.subscription_id,
                    display_name=sub.display_name,
                    state=str(sub.state) if sub.state else "Unknown",
                    tenant_id=self.tenant_id or "Unknown"
                ))
            subscription_client.close()
        except Exception as e:
            logger.error(f"Error getting subscriptions: {str(e)}")
            raise
        
        return subscriptions
    
    async def get_resource_client(self, subscription_id: str) -> ResourceManagementClient:
        """Get a resource management client for a specific subscription"""
        if not self.authenticated or not self.credential:
            raise ValueError("Not authenticated")
        
        return ResourceManagementClient(
            credential=self.credential,
            subscription_id=subscription_id
        )
    
    def get_graph_client(self) -> GraphServiceClient:
        """Get the Microsoft Graph client"""
        if not self.authenticated or not self.graph_client:
            raise ValueError("Not authenticated or Graph client not available")
        return self.graph_client
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated and not expired"""
        if not self.authenticated:
            return False
        
        if self.expires_at and datetime.now() >= self.expires_at:
            self.authenticated = False
            return False
            
        return True
    
    async def refresh_token(self) -> bool:
        """Refresh the authentication token if needed"""
        if not self.credential:
            return False
        
        try:
            token = self.credential.get_token("https://management.azure.com/.default")
            if token:
                self.expires_at = datetime.now() + timedelta(seconds=token.expires_on - int(datetime.now().timestamp()))
                return True
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            self.authenticated = False
            
        return False
    
    def close(self):
        """Close all connections"""
        if self.credential and hasattr(self.credential, 'close'):
            self.credential.close()
        if hasattr(self, '_clients'):
            for client in self._clients:
                if hasattr(client, 'close'):
                    client.close()

# Global auth instance
azure_auth = AzureAuth()