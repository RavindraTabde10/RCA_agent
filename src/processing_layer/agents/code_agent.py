"""
Code Agent - Specialized agent for code analysis
"""

from typing import Dict, Any, List
import logging
import json
from src.utils.llm_client import get_llm_client


class CodeAgent:
    """AI agent specialized in source code analysis"""
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.llm_config = llm_config or {}
        
        # Initialize LLM client
        try:
            self.llm_client = get_llm_client(llm_config)
            self.logger.info("Code Agent: LLM client initialized")
        except Exception as e:
            self.logger.warning(f"Code Agent: Failed to initialize LLM client: {str(e)}")
            self.llm_client = None
    
    def analyze(
        self, 
        code_context: Dict[str, Any],
        defect_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze source code for potential issues
        
        Args:
            code_context: Source code and related information
            defect_context: Context about the defect
            
        Returns:
            Analysis results with findings
        """
        self.logger.info("Code Agent: Starting analysis")
        
        results = {
            "agent": "code_agent",
            "findings": [],
            "confidence": 0.0,
            "code_issues": [],
            "suspicious_changes": [],
            "recommendations": []
        }
        
        # Analyze code structure
        if code_context.get("files"):
            structure_issues = self._analyze_code_structure(code_context["files"])
            results["code_issues"].extend(structure_issues)
        
        # Analyze recent changes
        if code_context.get("recent_changes"):
            change_analysis = self._analyze_changes(code_context["recent_changes"])
            results["suspicious_changes"].extend(change_analysis)
        
        # Check dependencies
        if code_context.get("dependencies"):
            dependency_issues = self._analyze_dependencies(code_context["dependencies"])
            results["code_issues"].extend(dependency_issues)
        
        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(
            results["code_issues"],
            results["suspicious_changes"]
        )
        
        # Calculate confidence
        results["confidence"] = self._calculate_confidence(results)
        
        self.logger.info(f"Code Agent: Found {len(results['code_issues'])} issues")
        
        return results
    
    def _analyze_code_structure(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze code structure for issues using LLM"""
        issues = []
        
        if not self.llm_client:
            self.logger.warning("LLM client not available, skipping code structure analysis")
            return issues
        
        for file_info in files:
            try:
                # Prepare context for LLM analysis
                code_snippet = file_info.get('content', '')
                file_path = file_info.get('path', 'unknown')
                
                if not code_snippet:
                    continue
                
                # Truncate code if too long (keep first 3000 chars)
                if len(code_snippet) > 3000:
                    code_snippet = code_snippet[:3000] + "\n... (truncated)"
                
                prompt = f"""Analyze the following code for potential issues, bugs, or anti-patterns:

File: {file_path}

Code:
```
{code_snippet}
```

Provide a JSON response with the following structure:
{{
    "issues": [
        {{
            "severity": "high|medium|low",
            "type": "bug|code_smell|performance|security",
            "description": "Description of the issue",
            "line": 0,
            "suggestion": "How to fix it"
        }}
    ]
}}

If no issues found, return {{"issues": []}}"""
                
                response = self.llm_client.analyze_text(
                    prompt=prompt,
                    system_message="You are an expert code reviewer specializing in identifying bugs and code quality issues. Always respond in valid JSON format.",
                    temperature=0.3
                )
                
                # Parse LLM response
                try:
                    analysis_result = json.loads(response)
                    for issue in analysis_result.get('issues', []):
                        issue['file'] = file_path
                        issues.append(issue)
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse LLM response for {file_path}")
                    
            except Exception as e:
                self.logger.error(f"Error analyzing code structure for {file_info.get('path')}: {str(e)}")
        
        return issues
    
    def _analyze_changes(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze recent code changes"""
        suspicious = []
        
        for change in changes:
            # Check if change is related to defect
            if self._is_potentially_problematic(change):
                suspicious.append({
                    "commit": change.get("commit_id"),
                    "author": change.get("author"),
                    "timestamp": change.get("timestamp"),
                    "reason": "Change coincides with defect timeline"
                })
        
        return suspicious
    
    def _is_potentially_problematic(self, change: Dict[str, Any]) -> bool:
        """Check if a change might be problematic"""
        # Placeholder logic
        return False
    
    def _analyze_dependencies(self, dependencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze dependency issues"""
        issues = []
        
        for dep in dependencies:
            # Check for version conflicts, deprecated packages, etc.
            pass
        
        return issues
    
    def _generate_recommendations(
        self,
        code_issues: List[Dict[str, Any]],
        suspicious_changes: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate code-related recommendations using LLM"""
        recommendations = []
        
        # Basic recommendations
        if code_issues:
            recommendations.append("Review identified code issues")
        
        if suspicious_changes:
            recommendations.append("Investigate recent code changes")
        
        # Use LLM to generate more specific recommendations
        if self.llm_client and (code_issues or suspicious_changes):
            try:
                context = {
                    "code_issues_count": len(code_issues),
                    "suspicious_changes_count": len(suspicious_changes),
                    "issues_summary": [issue.get('description', '') for issue in code_issues[:3]]
                }
                
                prompt = f"""Based on the following code analysis results, provide 3-5 specific, actionable recommendations for the development team:

Code Issues Found: {context['code_issues_count']}
Suspicious Changes: {context['suspicious_changes_count']}

Key Issues:
{json.dumps(context['issues_summary'], indent=2)}

Provide recommendations as a JSON array of strings:
{{"recommendations": ["recommendation 1", "recommendation 2", ...]}}"""
                
                response = self.llm_client.analyze_text(
                    prompt=prompt,
                    system_message="You are a senior software engineer providing actionable recommendations.",
                    temperature=0.5
                )
                
                try:
                    llm_recommendations = json.loads(response)
                    recommendations.extend(llm_recommendations.get('recommendations', []))
                except json.JSONDecodeError:
                    pass
                    
            except Exception as e:
                self.logger.error(f"Error generating LLM recommendations: {str(e)}")
        
        return recommendations
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        # Simplified confidence calculation
        evidence_count = len(results["code_issues"]) + len(results["suspicious_changes"])
        
        if evidence_count == 0:
            return 0.0
        
        return min(evidence_count * 0.15, 1.0)
