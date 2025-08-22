"""
Role Analysis Module

Analyzes Azure role assignments and categorizes them by identity type.
Provides detailed breakdown of roles assigned to different principal types.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.resource import ResourceManagementClient
from msgraph import GraphServiceClient
from auth import azure_auth

logger = logging.getLogger(__name__)


class RoleAnalyzer:
    """Analyzes Azure role assignments by identity type"""
    
    def __init__(self):
        self.auth_clients = {}
        self.resource_clients = {}
        
    def get_auth_client(self, subscription_id: str) -> AuthorizationManagementClient:
        """Get or create authorization management client for subscription"""
        if subscription_id not in self.auth_clients:
            self.auth_clients[subscription_id] = AuthorizationManagementClient(
                credential=azure_auth.credential,
                subscription_id=subscription_id
            )
        return self.auth_clients[subscription_id]
    
    def get_resource_client(self, subscription_id: str) -> ResourceManagementClient:
        """Get or create resource management client for subscription"""
        if subscription_id not in self.resource_clients:
            self.resource_clients[subscription_id] = ResourceManagementClient(
                credential=azure_auth.credential,
                subscription_id=subscription_id
            )
        return self.resource_clients[subscription_id]
    
    async def get_role_definitions(self, subscription_id: str) -> Dict[str, str]:
        """Get mapping of role definition IDs to role names"""
        try:
            auth_client = self.get_auth_client(subscription_id)
            role_definitions = {}
            
            for role_def in auth_client.role_definitions.list(scope=f"/subscriptions/{subscription_id}"):
                role_definitions[role_def.id] = role_def.role_name or role_def.name
                
            logger.info(f"Retrieved {len(role_definitions)} role definitions for subscription {subscription_id}")
            return role_definitions
            
        except Exception as e:
            logger.error(f"Error getting role definitions for subscription {subscription_id}: {str(e)}")
            return {}
    
    async def resolve_principal_types(self, principal_ids: List[str]) -> Dict[str, str]:
        """Resolve principal IDs to their types using Microsoft Graph"""
        principal_types = {}
        
        try:
            if not azure_auth.graph_client:
                logger.warning("Graph client not available, cannot resolve principal types")
                return {pid: "Unknown" for pid in principal_ids}
            
            # Batch resolve principals using Microsoft Graph
            for principal_id in principal_ids:
                try:
                    # Try to get as service principal first
                    try:
                        sp = azure_auth.graph_client.service_principals.by_service_principal_id(principal_id).get()
                        if sp:
                            # Check if it's a managed identity
                            if hasattr(sp, 'tags') and sp.tags and 'WindowsAzureActiveDirectoryIntegratedApp' in sp.tags:
                                principal_types[principal_id] = "ManagedIdentity"
                            else:
                                principal_types[principal_id] = "ServicePrincipal"
                            continue
                    except:
                        pass
                    
                    # Try to get as user
                    try:
                        user = azure_auth.graph_client.users.by_user_id(principal_id).get()
                        if user:
                            principal_types[principal_id] = "User"
                            continue
                    except:
                        pass
                    
                    # Try to get as group
                    try:
                        group = azure_auth.graph_client.groups.by_group_id(principal_id).get()
                        if group:
                            principal_types[principal_id] = "Group"
                            continue
                    except:
                        pass
                    
                    # If we can't resolve it, mark as Unknown/Deleted
                    principal_types[principal_id] = "Unknown or Deleted"
                    
                except Exception as e:
                    logger.warning(f"Could not resolve principal {principal_id}: {str(e)}")
                    principal_types[principal_id] = "Unknown or Deleted"
                    
        except Exception as e:
            logger.error(f"Error resolving principal types: {str(e)}")
            # Return Unknown for all if we can't resolve any
            return {pid: "Unknown" for pid in principal_ids}
        
        return principal_types
    
    async def analyze_role_assignments(self, subscription_ids: List[str]) -> Dict[str, Any]:
        """Analyze role assignments and categorize by identity type"""
        identity_breakdown = defaultdict(lambda: {"count": 0, "roles": defaultdict(int)})
        
        try:
            for subscription_id in subscription_ids:
                logger.info(f"Analyzing role assignments for subscription {subscription_id}")
                
                # Get role definitions for name mapping
                role_definitions = await self.get_role_definitions(subscription_id)
                
                # Get all role assignments
                auth_client = self.get_auth_client(subscription_id)
                assignments = []
                principal_ids = set()
                
                try:
                    for assignment in auth_client.role_assignments.list_for_subscription():
                        assignments.append({
                            'principal_id': assignment.principal_id,
                            'role_definition_id': assignment.role_definition_id,
                            'scope': assignment.scope
                        })
                        principal_ids.add(assignment.principal_id)
                        
                    logger.info(f"Found {len(assignments)} role assignments in subscription {subscription_id}")
                    
                except Exception as e:
                    logger.error(f"Error getting role assignments for subscription {subscription_id}: {str(e)}")
                    continue
                
                # Resolve principal types
                principal_types = await self.resolve_principal_types(list(principal_ids))
                
                # Categorize assignments
                for assignment in assignments:
                    principal_id = assignment['principal_id']
                    role_def_id = assignment['role_definition_id']
                    
                    # Get principal type
                    principal_type = principal_types.get(principal_id, "Unknown or Deleted")
                    
                    # Get role name
                    role_name = role_definitions.get(role_def_id, "Unknown Role")
                    
                    # Update counts
                    identity_breakdown[principal_type]["count"] += 1
                    identity_breakdown[principal_type]["roles"][role_name] += 1
            
            # Convert defaultdict to regular dict for JSON serialization
            result = {}
            for identity_type, data in identity_breakdown.items():
                result[identity_type] = {
                    "count": data["count"],
                    "roles": dict(data["roles"])
                }
            
            logger.info(f"Identity breakdown completed: {len(result)} identity types found")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing role assignments: {str(e)}")
            return {}
    
    def close_clients(self):
        """Close all clients"""
        try:
            for client in self.auth_clients.values():
                if hasattr(client, 'close'):
                    client.close()
                    
            for client in self.resource_clients.values():
                if hasattr(client, 'close'):
                    client.close()
                    
        except Exception as e:
            logger.error(f"Error closing role analyzer clients: {str(e)}")


# Global analyzer instance
role_analyzer = RoleAnalyzer()


async def get_detailed_identity_roles(subscription_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get detailed role assignments grouped by identity type
    
    Args:
        subscription_ids: List of Azure subscription IDs to analyze
        
    Returns:
        Dictionary with detailed role assignments by identity type
    """
    detailed_assignments = {
        "users": [],
        "service_principals": [],
        "managed_identities": [],
        "groups": [],
        "unknown_or_deleted": []
    }
    
    try:
        for subscription_id in subscription_ids:
            logger.info(f"Getting detailed role assignments for subscription {subscription_id}")
            
            # Get role definitions for name mapping
            role_definitions = await role_analyzer.get_role_definitions(subscription_id)
            
            # Get all role assignments
            auth_client = role_analyzer.get_auth_client(subscription_id)
            assignments = []
            principal_ids = set()
            
            try:
                for assignment in auth_client.role_assignments.list_for_subscription():
                    assignments.append({
                        'principal_id': assignment.principal_id,
                        'role_definition_id': assignment.role_definition_id,
                        'scope': assignment.scope
                    })
                    principal_ids.add(assignment.principal_id)
                    
                logger.info(f"Found {len(assignments)} role assignments in subscription {subscription_id}")
                
            except Exception as e:
                logger.error(f"Error getting role assignments for subscription {subscription_id}: {str(e)}")
                continue
            
            # Resolve principal types
            principal_types = await role_analyzer.resolve_principal_types(list(principal_ids))
            
            # Categorize detailed assignments
            for assignment in assignments:
                principal_id = assignment['principal_id']
                role_def_id = assignment['role_definition_id']
                scope = assignment['scope']
                
                # Get principal type
                principal_type = principal_types.get(principal_id, "Unknown or Deleted")
                
                # Get role name
                role_name = role_definitions.get(role_def_id, "Unknown Role")
                
                # Create detailed assignment object
                detailed_assignment = {
                    "principal_id": principal_id,
                    "principal_name": None,  # Could be enhanced to resolve names
                    "principal_type": principal_type,
                    "role_definition_name": role_name,
                    "scope": scope,
                    "subscription_id": subscription_id
                }
                
                # Add to appropriate category
                if principal_type == "User":
                    detailed_assignments["users"].append(detailed_assignment)
                elif principal_type == "ServicePrincipal":
                    detailed_assignments["service_principals"].append(detailed_assignment)
                elif principal_type == "ManagedIdentity":
                    detailed_assignments["managed_identities"].append(detailed_assignment)
                elif principal_type == "Group":
                    detailed_assignments["groups"].append(detailed_assignment)
                else:
                    detailed_assignments["unknown_or_deleted"].append(detailed_assignment)
        
        logger.info(f"Detailed identity analysis completed: {sum(len(v) for v in detailed_assignments.values())} total assignments")
        return detailed_assignments
        
    except Exception as e:
        logger.error(f"Error getting detailed identity roles: {str(e)}")
        return detailed_assignments

async def summarize_identity_roles(subscription_ids: List[str]) -> Dict[str, Any]:
    """
    Main function to summarize role assignments by identity type
    
    Args:
        subscription_ids: List of Azure subscription IDs to analyze
        
    Returns:
        Dictionary with identity type breakdown and role counts
    """
    return await role_analyzer.analyze_role_assignments(subscription_ids)