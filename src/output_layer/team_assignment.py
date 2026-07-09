"""
Team Assignment - Assigns defects to appropriate teams
"""

from typing import Dict, Any, List, Optional
import logging


class TeamAssignment:
    """Intelligently assigns defects to the appropriate team"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.teams = self._load_teams()
    
    def _load_teams(self) -> List[Dict[str, Any]]:
        """Load team information"""
        # Default teams with their expertise
        return [
            {
                "id": "BACKEND",
                "name": "Backend Engineering",
                "skills": ["api", "database", "server", "backend", "performance"],
                "capacity": 10
            },
            {
                "id": "FRONTEND",
                "name": "Frontend Engineering",
                "skills": ["ui", "ux", "frontend", "javascript", "react", "vue"],
                "capacity": 8
            },
            {
                "id": "DEVOPS",
                "name": "DevOps",
                "skills": ["deployment", "infrastructure", "ci/cd", "docker", "kubernetes"],
                "capacity": 5
            },
            {
                "id": "DATABASE",
                "name": "Database Team",
                "skills": ["sql", "database", "query", "performance", "schema"],
                "capacity": 6
            },
            {
                "id": "SECURITY",
                "name": "Security Team",
                "skills": ["security", "authentication", "authorization", "vulnerability"],
                "capacity": 4
            },
            {
                "id": "MOBILE",
                "name": "Mobile Engineering",
                "skills": ["mobile", "ios", "android", "app"],
                "capacity": 7
            }
        ]
    
    def assign_team(
        self,
        defect_data: Dict[str, Any],
        diagnosis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assign defect to the most appropriate team
        
        Args:
            defect_data: Defect information
            diagnosis: Diagnosis results
            
        Returns:
            Assignment information
        """
        self.logger.info(f"Assigning team for defect: {defect_data.get('id')}")
        
        # Calculate match scores for each team
        team_scores = []
        
        for team in self.teams:
            score = self._calculate_team_match(team, defect_data, diagnosis)
            team_scores.append({
                "team": team,
                "score": score,
                "reasons": self._explain_match(team, defect_data, diagnosis, score)
            })
        
        # Sort by score
        team_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Get top team
        best_match = team_scores[0]
        
        assignment = {
            "defect_id": defect_data.get("id"),
            "assigned_team_id": best_match["team"]["id"],
            "assigned_team_name": best_match["team"]["name"],
            "confidence": best_match["score"],
            "reasons": best_match["reasons"],
            "alternative_teams": [
                {
                    "team_id": ts["team"]["id"],
                    "team_name": ts["team"]["name"],
                    "score": ts["score"]
                }
                for ts in team_scores[1:3]  # Top 2 alternatives
            ]
        }
        
        self.logger.info(
            f"Assigned to {assignment['assigned_team_name']} "
            f"with confidence {assignment['confidence']:.2%}"
        )
        
        return assignment
    
    def _calculate_team_match(
        self,
        team: Dict[str, Any],
        defect_data: Dict[str, Any],
        diagnosis: Dict[str, Any]
    ) -> float:
        """Calculate how well a team matches the defect"""
        score = 0.0
        
        # Combine relevant text from defect and diagnosis
        relevant_text = " ".join([
            defect_data.get("description", ""),
            defect_data.get("title", ""),
            diagnosis.get("root_cause", "")
        ]).lower()
        
        # Check skill matches
        team_skills = team.get("skills", [])
        matches = sum(1 for skill in team_skills if skill in relevant_text)
        
        if team_skills:
            score = matches / len(team_skills)
        
        # Adjust for team capacity
        capacity = team.get("capacity", 0)
        if capacity < 3:
            score *= 0.8  # Reduce score for overloaded teams
        
        return min(score, 1.0)
    
    def _explain_match(
        self,
        team: Dict[str, Any],
        defect_data: Dict[str, Any],
        diagnosis: Dict[str, Any],
        score: float
    ) -> List[str]:
        """Explain why this team was matched"""
        reasons = []
        
        relevant_text = " ".join([
            defect_data.get("description", ""),
            diagnosis.get("root_cause", "")
        ]).lower()
        
        # Find which skills matched
        matched_skills = [
            skill for skill in team.get("skills", [])
            if skill in relevant_text
        ]
        
        if matched_skills:
            reasons.append(f"Team has expertise in: {', '.join(matched_skills)}")
        
        if score > 0.7:
            reasons.append("Strong match based on defect characteristics")
        elif score > 0.4:
            reasons.append("Moderate match based on available information")
        else:
            reasons.append("Assigned by default due to limited match information")
        
        return reasons
    
    def get_team_workload(self, team_id: str) -> Dict[str, Any]:
        """Get current workload for a team"""
        team = next((t for t in self.teams if t["id"] == team_id), None)
        
        if not team:
            return {"error": "Team not found"}
        
        return {
            "team_id": team_id,
            "team_name": team["name"],
            "capacity": team.get("capacity", 0),
            "current_load": 0,  # Placeholder
            "available_capacity": team.get("capacity", 0)
        }
    
    def suggest_escalation(
        self,
        defect_data: Dict[str, Any],
        diagnosis: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Determine if defect should be escalated"""
        should_escalate = False
        reasons = []
        
        # Check severity
        if defect_data.get("severity") in ["critical", "high"]:
            should_escalate = True
            reasons.append("High severity defect")
        
        # Check confidence
        if diagnosis.get("confidence", 0) < 0.3:
            should_escalate = True
            reasons.append("Low confidence in diagnosis")
        
        # Check impact
        impact = diagnosis.get("impact", {})
        if impact.get("business_impact") == "critical":
            should_escalate = True
            reasons.append("Critical business impact")
        
        if should_escalate:
            return {
                "should_escalate": True,
                "reasons": reasons,
                "escalate_to": "Engineering Management"
            }
        
        return None
