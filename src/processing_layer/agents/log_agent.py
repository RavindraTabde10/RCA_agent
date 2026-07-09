"""
Log Agent - Specialized agent for log analysis
"""

from typing import Dict, Any, List
import logging
import json
from src.utils.llm_client import get_llm_client


class LogAgent:
    """AI agent specialized in analyzing log data"""
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.llm_config = llm_config or {}
        
        # Initialize LLM client
        try:
            self.llm_client = get_llm_client(llm_config)
            self.logger.info("Log Agent: LLM client initialized")
        except Exception as e:
            self.logger.warning(f"Log Agent: Failed to initialize LLM client: {str(e)}")
            self.llm_client = None
    
    def analyze(self, log_data: Dict[str, Any], defect_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze log data to identify potential root causes
        
        Args:
            log_data: Processed log information
            defect_context: Context about the defect
            
        Returns:
            Analysis results with findings
        """
        self.logger.info("Log Agent: Starting analysis")
        
        results = {
            "agent": "log_agent",
            "findings": [],
            "confidence": 0.0,
            "evidence": [],
            "hypotheses": []
        }
        
        # Analyze errors
        if log_data.get("errors"):
            error_findings = self._analyze_errors(log_data["errors"])
            results["findings"].extend(error_findings)
        
        # Analyze exceptions
        if log_data.get("exceptions"):
            exception_findings = self._analyze_exceptions(log_data["exceptions"])
            results["findings"].extend(exception_findings)
        
        # Look for patterns
        if log_data.get("patterns"):
            pattern_findings = self._analyze_patterns(log_data["patterns"])
            results["findings"].extend(pattern_findings)
        
        # Calculate confidence based on findings
        results["confidence"] = self._calculate_confidence(results["findings"])
        
        # Generate hypotheses
        results["hypotheses"] = self._generate_hypotheses(results["findings"])
        
        self.logger.info(f"Log Agent: Found {len(results['findings'])} findings")
        
        return results
    
    def _analyze_errors(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze error messages using LLM"""
        findings = []
        
        for error in errors:
            finding = {
                "type": "error",
                "severity": "high",
                "description": f"Error detected: {error.get('message', 'Unknown')}",
                "timestamp": error.get("timestamp"),
                "evidence": error
            }
            
            # Use LLM to get deeper analysis if available
            if self.llm_client:
                try:
                    error_message = error.get('message', '')
                    prompt = f"""Analyze this error message and provide insights:

Error: {error_message}

Provide a JSON response:
{{
    "root_cause_hypothesis": "Likely root cause",
    "severity_assessment": "critical|high|medium|low",
    "impact": "Description of impact",
    "recommended_action": "What to do next"
}}"""
                    
                    response = self.llm_client.analyze_text(
                        prompt=prompt,
                        system_message="You are an expert in analyzing application logs and errors.",
                        temperature=0.3
                    )
                    
                    try:
                        analysis = json.loads(response)
                        finding['llm_analysis'] = analysis
                        finding['severity'] = analysis.get('severity_assessment', 'high')
                    except json.JSONDecodeError:
                        pass
                        
                except Exception as e:
                    self.logger.error(f"Error analyzing error with LLM: {str(e)}")
            
            findings.append(finding)
        
        return findings
    
    def _analyze_exceptions(self, exceptions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze exception traces using LLM"""
        findings = []
        
        for exception in exceptions:
            finding = {
                "type": "exception",
                "severity": "critical",
                "description": f"Exception detected: {exception.get('message', 'Unknown')}",
                "stack_trace": exception.get("stack_trace"),
                "evidence": exception
            }
            
            # Use LLM to analyze stack trace
            if self.llm_client and exception.get('stack_trace'):
                try:
                    stack_trace = exception.get('stack_trace', '')
                    # Truncate if too long
                    if len(stack_trace) > 2000:
                        stack_trace = stack_trace[:2000] + "\n... (truncated)"
                    
                    prompt = f"""Analyze this exception stack trace:

Exception: {exception.get('message', 'Unknown')}

Stack Trace:
{stack_trace}

Provide a JSON response:
{{
    "likely_cause": "Most likely cause of this exception",
    "problematic_component": "Which component/module is affected",
    "fix_suggestion": "How to fix this issue",
    "prevention": "How to prevent this in future"
}}"""
                    
                    response = self.llm_client.analyze_text(
                        prompt=prompt,
                        system_message="You are an expert in debugging and analyzing exception stack traces.",
                        temperature=0.3
                    )
                    
                    try:
                        analysis = json.loads(response)
                        finding['llm_analysis'] = analysis
                    except json.JSONDecodeError:
                        pass
                        
                except Exception as e:
                    self.logger.error(f"Error analyzing exception with LLM: {str(e)}")
            
            findings.append(finding)
        
        return findings
    
    def _analyze_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze recurring patterns"""
        findings = []
        
        for pattern in patterns:
            finding = {
                "type": "pattern",
                "severity": "medium",
                "description": f"Recurring pattern detected",
                "frequency": pattern.get("frequency"),
                "evidence": pattern
            }
            findings.append(finding)
        
        return findings
    
    def _calculate_confidence(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on findings"""
        if not findings:
            return 0.0
        
        # Simple confidence calculation
        # In production, use more sophisticated scoring
        critical_findings = sum(1 for f in findings if f.get("severity") == "critical")
        high_findings = sum(1 for f in findings if f.get("severity") == "high")
        
        score = (critical_findings * 0.3 + high_findings * 0.2) / len(findings)
        return min(score, 1.0)
    
    def _generate_hypotheses(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate hypotheses based on findings"""
        hypotheses = []
        
        # Generate hypotheses from findings
        if any(f.get("type") == "exception" for f in findings):
            hypotheses.append("Application may be encountering runtime exceptions")
        
        if any(f.get("type") == "pattern" for f in findings):
            hypotheses.append("Issue appears to be recurring systematically")
        
        return hypotheses
