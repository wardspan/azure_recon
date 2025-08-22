import asyncio
import logging
from typing import List, Dict, Any
from azure.mgmt.authorization import AuthorizationManagementClient
from msgraph import GraphServiceClient
from msgraph.generated.users.users_request_builder import UsersRequestBuilder
from msgraph.generated.directory_roles.directory_roles_request_builder import DirectoryRolesRequestBuilder
from auth import azure_auth
from models import UserInfo, RoleAssignment

logger = logging.getLogger(__name__)

class IdentityAnalyzer:
    def __init__(self):
        self.auth_clients: Dict[str, AuthorizationManagementClient] = {}
    
    def get_auth_client(self, subscription_id: str) -> AuthorizationManagementClient:
        """Get or create an Authorization Management client for a subscription"""
        if subscription_id not in self.auth_clients:
            if not azure_auth.is_authenticated():
                raise ValueError("Not authenticated with Azure")
            
            self.auth_clients[subscription_id] = AuthorizationManagementClient(
                credential=azure_auth.credential,
                subscription_id=subscription_id
            )
        
        return self.auth_clients[subscription_id]
    
    async def get_users_info(self) -> List[UserInfo]:
        """Get information about users in the tenant"""
        users = []
        
        try:
            graph_client = azure_auth.get_graph_client()
            
            # Get all users
            users_collection = graph_client.users.get()
            if users_collection and users_collection.value:
                for user in users_collection.value[:100]:  # Limit to first 100 users
                    try:
                        # Check MFA status (this is a simplified approach)
                        mfa_enabled = False
                        try:
                            # Try to get authentication methods
                            auth_methods = graph_client.users.by_user_id(user.id).authentication.methods.get()
                            if auth_methods and auth_methods.value:
                                mfa_enabled = len(auth_methods.value) > 1
                        except:
                            # If we can't get auth methods, assume MFA is disabled
                            pass
                        
                        # Get sign-in activity (simplified)
                        sign_in_activity = None
                        try:
                            # This would require additional permissions in a real implementation
                            sign_in_activity = {
                                'last_sign_in': None,
                                'last_non_interactive_sign_in': None
                            }
                        except:
                            pass
                        
                        user_info = UserInfo(
                            id=user.id,
                            display_name=user.display_name or "Unknown",
                            user_principal_name=user.user_principal_name or "Unknown",
                            mail=user.mail,
                            is_guest=user.user_type == "Guest" if user.user_type else False,
                            mfa_enabled=mfa_enabled,
                            sign_in_activity=sign_in_activity
                        )
                        users.append(user_info)
                        
                    except Exception as e:
                        logger.warning(f"Error processing user {user.id}: {str(e)}")
                        continue
            
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
        
        return users
    
    async def get_role_assignments(self, subscription_ids: List[str]) -> List[RoleAssignment]:
        """Get role assignments across subscriptions"""
        role_assignments = []
        
        for subscription_id in subscription_ids:
            try:
                auth_client = self.get_auth_client(subscription_id)
                
                # Get all role assignments in the subscription
                for assignment in auth_client.role_assignments.list(
                    filter=f"atScope()"
                ):
                    try:
                        # Get role definition details
                        role_definition = None
                        if assignment.role_definition_id:
                            try:
                                role_definition = auth_client.role_definitions.get_by_id(
                                    assignment.role_definition_id
                                )
                            except:
                                pass
                        
                        # Get principal information
                        principal_name = "Unknown"
                        principal_type = "Unknown"
                        
                        if assignment.principal_id:
                            try:
                                # Try to get principal info from Graph API
                                graph_client = azure_auth.get_graph_client()
                                
                                # Try as user first
                                try:
                                    principal = graph_client.users.by_user_id(assignment.principal_id).get()
                                    if principal:
                                        principal_name = principal.display_name or principal.user_principal_name or "Unknown User"
                                        principal_type = "User"
                                except:
                                    # Try as service principal
                                    try:
                                        principal = graph_client.service_principals.by_service_principal_id(assignment.principal_id).get()
                                        if principal:
                                            principal_name = principal.display_name or "Unknown Service Principal"
                                            principal_type = "ServicePrincipal"
                                    except:
                                        # Try as group
                                        try:
                                            principal = graph_client.groups.by_group_id(assignment.principal_id).get()
                                            if principal:
                                                principal_name = principal.display_name or "Unknown Group"
                                                principal_type = "Group"
                                        except:
                                            pass
                            except:
                                pass
                        
                        role_name = "Unknown Role"
                        if role_definition and role_definition.role_name:
                            role_name = role_definition.role_name
                        elif assignment.role_definition_id:
                            # Extract role name from ID if possible
                            role_id_parts = assignment.role_definition_id.split('/')
                            if role_id_parts:
                                role_name = role_id_parts[-1]
                        
                        role_assignment = RoleAssignment(
                            principal_id=assignment.principal_id or "Unknown",
                            principal_name=principal_name,
                            principal_type=principal_type,
                            role_definition_name=role_name,
                            scope=assignment.scope or f"/subscriptions/{subscription_id}",
                            subscription_id=subscription_id
                        )
                        role_assignments.append(role_assignment)
                        
                    except Exception as e:
                        logger.warning(f"Error processing role assignment: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not get role assignments for subscription {subscription_id}: {str(e)}")
                continue
        
        return role_assignments
    
    async def get_privileged_roles(self) -> List[Dict[str, Any]]:
        """Get users with privileged directory roles"""
        privileged_roles = []
        
        try:
            graph_client = azure_auth.get_graph_client()
            
            # Get directory roles
            directory_roles = graph_client.directory_roles.get()
            if directory_roles and directory_roles.value:
                for role in directory_roles.value:
                    # Focus on high-privilege roles
                    privileged_role_names = [
                        'Global Administrator',
                        'Privileged Role Administrator',
                        'Security Administrator',
                        'User Administrator',
                        'Application Administrator',
                        'Cloud Application Administrator',
                        'Authentication Administrator',
                        'Privileged Authentication Administrator'
                    ]
                    
                    if role.display_name in privileged_role_names:
                        try:
                            # Get members of this role
                            members = graph_client.directory_roles.by_directory_role_id(role.id).members.get()
                            if members and members.value:
                                privileged_roles.append({
                                    'role_name': role.display_name,
                                    'role_id': role.id,
                                    'member_count': len(members.value),
                                    'members': [
                                        {
                                            'id': member.id,
                                            'display_name': getattr(member, 'display_name', 'Unknown'),
                                            'user_principal_name': getattr(member, 'user_principal_name', None)
                                        }
                                        for member in members.value[:10]  # Limit to first 10 members
                                    ]
                                })
                        except Exception as e:
                            logger.warning(f"Error getting members for role {role.display_name}: {str(e)}")
                            
        except Exception as e:
            logger.error(f"Error getting privileged roles: {str(e)}")
        
        return privileged_roles
    
    def close_clients(self):
        """Close all authorization clients"""
        for client in self.auth_clients.values():
            if hasattr(client, 'close'):
                client.close()
        self.auth_clients.clear()

# Global analyzer instance
identity_analyzer = IdentityAnalyzer()