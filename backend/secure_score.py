import asyncio
import logging
from typing import List, Dict, Any
from azure.mgmt.security import SecurityCenter
from auth import azure_auth
from models import SecureScoreData, Recommendation

logger = logging.getLogger(__name__)

class SecureScoreAnalyzer:
    def __init__(self):
        self.security_clients: Dict[str, SecurityCenter] = {}
    
    def get_security_client(self, subscription_id: str) -> SecurityCenter:
        """Get or create a Security Center client for a subscription"""
        if subscription_id not in self.security_clients:
            if not azure_auth.is_authenticated():
                raise ValueError("Not authenticated with Azure")
            
            self.security_clients[subscription_id] = SecurityCenter(
                credential=azure_auth.credential,
                subscription_id=subscription_id
            )
        
        return self.security_clients[subscription_id]
    
    async def get_secure_scores(self, subscription_ids: List[str]) -> SecureScoreData:
        """Get secure scores across all subscriptions"""
        try:
            total_current_score = 0.0
            total_max_score = 0.0
            control_scores = []
            
            for subscription_id in subscription_ids:
                try:
                    security_client = self.get_security_client(subscription_id)
                    
                    # Get secure scores
                    secure_scores = []
                    for score in security_client.secure_scores.list():
                        secure_scores.append(score)
                    
                    if secure_scores:
                        for score in secure_scores:
                            if hasattr(score, 'properties'):
                                props = score.properties
                                current_score = getattr(props, 'current_score', 0)
                                max_score = getattr(props, 'max_score', 0)
                                
                                total_current_score += current_score
                                total_max_score += max_score
                                
                                control_scores.append({
                                    'subscription_id': subscription_id,
                                    'score_name': score.name,
                                    'display_name': getattr(props, 'display_name', 'Unknown'),
                                    'current_score': current_score,
                                    'max_score': max_score,
                                    'percentage': (current_score / max_score * 100) if max_score > 0 else 0
                                })
                    
                except Exception as e:
                    logger.warning(f"Could not get secure scores for subscription {subscription_id}: {str(e)}")
                    continue
            
            percentage = (total_current_score / total_max_score * 100) if total_max_score > 0 else 0
            
            return SecureScoreData(
                current_score=total_current_score,
                max_score=total_max_score,
                percentage=percentage,
                control_scores=control_scores
            )
            
        except Exception as e:
            logger.error(f"Error getting secure scores: {str(e)}")
            # Return default values if we can't get real data
            return SecureScoreData(
                current_score=0.0,
                max_score=100.0,
                percentage=0.0,
                control_scores=[]
            )
    
    async def get_security_recommendations(self, subscription_ids: List[str]) -> List[Recommendation]:
        """Get security recommendations from Microsoft Defender for Cloud"""
        recommendations = []
        
        for subscription_id in subscription_ids:
            try:
                security_client = self.get_security_client(subscription_id)
                
                # Get assessments (recommendations)
                for assessment in security_client.assessments.list():
                    try:
                        if hasattr(assessment, 'properties'):
                            props = assessment.properties
                            
                            # Get affected resources count
                            affected_resources = 0
                            try:
                                for resource in security_client.sub_assessments.list_all(
                                    assessment_name=assessment.name
                                ):
                                    affected_resources += 1
                            except:
                                # If we can't get sub-assessments, estimate based on status
                                affected_resources = 1 if getattr(props, 'status', {}).get('code') != 'Healthy' else 0
                            
                            recommendation = Recommendation(
                                id=assessment.id or f"assessment_{len(recommendations)}",
                                name=assessment.name or "Unknown Assessment",
                                description=getattr(props, 'display_name', 'No description available'),
                                severity=getattr(getattr(props, 'metadata', {}), 'severity', 'Medium'),
                                category=getattr(getattr(props, 'metadata', {}), 'categories', ['General'])[0] if getattr(getattr(props, 'metadata', {}), 'categories', None) else 'General',
                                state=getattr(getattr(props, 'status', {}), 'code', 'Unknown'),
                                affected_resources=affected_resources
                            )
                            recommendations.append(recommendation)
                            
                    except Exception as e:
                        logger.warning(f"Error processing assessment {assessment.name}: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not get recommendations for subscription {subscription_id}: {str(e)}")
                continue
        
        return recommendations
    
    def close_clients(self):
        """Close all security clients"""
        for client in self.security_clients.values():
            if hasattr(client, 'close'):
                client.close()
        self.security_clients.clear()

# Global analyzer instance
secure_score_analyzer = SecureScoreAnalyzer()