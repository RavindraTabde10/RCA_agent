"""
LLM Service - Integration with LLM APIs for Root Cause Analysis

PLACEHOLDER: This module contains placeholder methods for LLM API integration.
The actual implementation will use your organization's LLM API credentials.

Supported Providers (placeholder implementations):
- Azure OpenAI
- OpenAI
- Custom/Local LLM endpoints
"""

import os
import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

# Import domain configuration
try:
    from rca_infotainment.domain_config import get_domain_config, get_llm_system_suffix, is_automotive
except ImportError:
    # Fallback if domain_config not available
    def get_domain_config():
        return None
    def get_llm_system_suffix():
        return ""
    def is_automotive():
        return True


class BaseLLMService(ABC):
    """Base class for LLM services"""
    
    @abstractmethod
    def analyze(self, prompt: str, system_message: str = None) -> str:
        """Run analysis with LLM"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        pass


class LLMService(BaseLLMService):
    """
    LLM Integration Service for RCA
    
    PLACEHOLDER: Configure with your LLM API credentials.
    
    Supported configurations:
    1. Azure OpenAI:
       - AZURE_OPENAI_ENDPOINT
       - AZURE_OPENAI_API_KEY
       - AZURE_OPENAI_DEPLOYMENT_NAME
       
    2. OpenAI:
       - OPENAI_API_KEY
       
    3. Custom Endpoint:
       - LLM_ENDPOINT_URL
       - LLM_API_KEY
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize LLM Service
        
        Args:
            config: Configuration dictionary with LLM settings
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # LLM Configuration
        llm_config = config.get('llm', {})
        self.provider = llm_config.get('provider', 'placeholder')
        
        # Azure OpenAI settings
        self.azure_endpoint = llm_config.get('azure_endpoint') or os.getenv('AZURE_OPENAI_ENDPOINT', '')
        self.azure_key = llm_config.get('azure_api_key') or os.getenv('AZURE_OPENAI_API_KEY', '')
        self.azure_deployment = llm_config.get('deployment_name') or os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')
        self.azure_api_version = llm_config.get('api_version') or os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        
        # OpenAI settings
        self.openai_key = llm_config.get('openai_api_key') or os.getenv('OPENAI_API_KEY', '')
        
        # Custom endpoint settings
        self.custom_endpoint = llm_config.get('endpoint_url') or os.getenv('LLM_ENDPOINT_URL', '')
        self.custom_key = llm_config.get('api_key') or os.getenv('LLM_API_KEY', '')
        
        # Model settings
        self.model = llm_config.get('model', 'gpt-4')
        self.temperature = llm_config.get('temperature', 0.3)
        self.max_tokens = llm_config.get('max_tokens', 4000)
        
        # Initialize appropriate client
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize LLM client based on configuration"""
        try:
            if self.provider == 'azure_openai' or self.azure_endpoint:
                self._init_azure_openai()
            elif self.provider == 'openai' or self.openai_key:
                self._init_openai()
            elif self.custom_endpoint:
                self._init_custom()
            else:
                self.logger.warning("No LLM configuration found - using placeholder mode")
                self.provider = 'placeholder'
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM client: {e}")
            self.provider = 'placeholder'
    
    def _init_azure_openai(self):
        """Initialize Azure OpenAI client"""
        if not self.azure_endpoint or not self.azure_key:
            raise ValueError("Azure OpenAI endpoint and API key required")
        
        try:
            # Use generic OpenAI client with custom base URL for APIM compatibility
            # This matches the approach in LLMClient that works with APIM gateways
            from openai import OpenAI
            
            # Construct base URL: {endpoint}/deployments/{deployment_name}
            # This format works with Azure API Management (APIM) gateways
            base_url = f"{self.azure_endpoint}/deployments/{self.azure_deployment}"
            
            self._client = OpenAI(
                base_url=base_url,
                api_key=self.azure_key,
                default_headers={
                    "api-key": self.azure_key
                },
                default_query={
                    "api-version": self.azure_api_version
                }
            )
            self.provider = 'azure_openai'
            self.logger.info(f"Azure OpenAI client initialized: {self.azure_endpoint}")
            self.logger.info(f"Base URL: {base_url}")
            self.logger.info(f"Deployment: {self.azure_deployment}")
        except ImportError:
            self.logger.error("openai package not installed. Run: pip install openai")
            raise
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        if not self.openai_key:
            raise ValueError("OpenAI API key required")
        
        try:
            from openai import OpenAI
            
            self._client = OpenAI(api_key=self.openai_key)
            self.provider = 'openai'
            self.logger.info("OpenAI client initialized")
        except ImportError:
            self.logger.error("openai package not installed. Run: pip install openai")
            raise
    
    def _init_custom(self):
        """Initialize custom LLM endpoint"""
        self.provider = 'custom'
        self.logger.info(f"Custom LLM endpoint configured: {self.custom_endpoint}")
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.provider != 'placeholder' and self._client is not None
    
    def analyze(
        self, 
        prompt: str, 
        system_message: str = None
    ) -> str:
        """
        Run analysis with LLM
        
        PLACEHOLDER: Replace with actual LLM API call
        
        Args:
            prompt: User prompt with analysis request
            system_message: Optional system message for context
            
        Returns:
            LLM response text
        """
        if not system_message:
            system_message = self._get_default_system_message()
        
        if self.provider == 'placeholder':
            return self._get_placeholder_response(prompt)
        
        try:
            if self.provider in ('azure_openai', 'openai'):
                return self._call_openai(prompt, system_message)
            elif self.provider == 'custom':
                return self._call_custom(prompt, system_message)
            else:
                return self._get_placeholder_response(prompt)
                
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return self._get_error_response(str(e))
    
    def analyze_text(self, prompt: str, system_message: str = None) -> str:
        """
        Alias for analyze() method - for compatibility with RCA engine
        
        Args:
            prompt: User prompt with analysis request
            system_message: Optional system message for context
            
        Returns:
            LLM response text
        """
        return self.analyze(prompt, system_message)
    
    def _call_openai(self, prompt: str, system_message: str) -> str:
        """Call OpenAI/Azure OpenAI API"""
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        params = {
            "model": self.azure_deployment if self.provider == 'azure_openai' else self.model,
            "messages": messages,
            "temperature": self.temperature
        }
        
        # For newer models (GPT-4o, GPT-5, etc.), use max_completion_tokens
        # For older models, use max_tokens
        # Check if model name suggests it's a newer model
        model_name = self.azure_deployment if self.provider == 'azure_openai' else self.model
        if any(x in model_name.lower() for x in ['gpt-5', 'gpt-4o', 'o1', 'o3']):
            params["max_completion_tokens"] = self.max_tokens
        else:
            params["max_tokens"] = self.max_tokens
        
        response = self._client.chat.completions.create(**params)
        return response.choices[0].message.content
    
    def _call_custom(self, prompt: str, system_message: str) -> str:
        """Call custom LLM endpoint"""
        import requests
        
        payload = {
            "prompt": prompt,
            "system_message": system_message,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.custom_key:
            headers["Authorization"] = f"Bearer {self.custom_key}"
        
        response = requests.post(
            self.custom_endpoint, 
            json=payload, 
            headers=headers,
            timeout=120
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get('response', data.get('content', data.get('text', str(data))))
    
    def _get_default_system_message(self) -> str:
        """Get default system message for RCA based on domain."""
        # Get domain-specific configuration
        domain_config = get_domain_config()
        domain_suffix = get_llm_system_suffix()
        
        # Base message
        base_message = """You are an expert software engineer specializing in Root Cause Analysis (RCA).
Your task is to analyze defect information and provide:
1. Clear root cause identification
2. Evidence supporting your conclusion  
3. Specific code files that need to be fixed
4. Detailed fix recommendations
5. Confidence level in your analysis
6. Preventive measures for the future

Be specific, technical, and actionable in your responses."""
        
        # Add domain-specific context
        if domain_config:
            domain_context = f"""

--- DOMAIN CONTEXT: {domain_config.display_name} ---
{domain_suffix}

Key components to analyze: {', '.join(domain_config.component_keywords.keys())}
Common root causes in this domain: {', '.join(domain_config.common_root_causes[:5])}
"""
            return base_message + domain_context
        
        # Fallback to automotive-specific message for backward compatibility
        return """You are an expert automotive infotainment software engineer specializing in:
- DLT (Diagnostic Log and Trace) log analysis
- Root Cause Analysis (RCA) for complex embedded systems
- Audio/Media subsystems, Bluetooth connectivity, CAN bus communication
- System boot and initialization sequences
- Memory management and threading issues

Your task is to analyze defect information and provide:
1. Clear root cause identification
2. Evidence supporting your conclusion
3. Specific code files that need to be fixed
4. Detailed fix recommendations
5. Confidence level in your analysis
6. Preventive measures for the future

Be specific, technical, and actionable in your responses."""
    
    def _get_placeholder_response(self, prompt: str) -> str:
        """Generate placeholder response when LLM is not configured"""
        return """## ROOT CAUSE
LLM API is not configured. This is a placeholder response.

To enable LLM-powered analysis, configure one of the following:

1. **Azure OpenAI:**
   - Set AZURE_OPENAI_ENDPOINT
   - Set AZURE_OPENAI_API_KEY
   - Set AZURE_OPENAI_DEPLOYMENT_NAME

2. **OpenAI:**
   - Set OPENAI_API_KEY

3. **Custom Endpoint:**
   - Set LLM_ENDPOINT_URL
   - Set LLM_API_KEY (optional)

## EVIDENCE
- Unable to analyze without LLM configuration
- Review DLT logs manually for error patterns
- Check source code mapping for affected files

## AFFECTED CODE
- See source mapping section in report

## FIX RECOMMENDATION
Configure LLM API to get AI-powered fix recommendations.

## CONFIDENCE
30%

## PREVENTIVE MEASURES
- Configure LLM API for automated analysis
- Add comprehensive logging
- Implement automated tests
"""
    
    def _get_error_response(self, error: str) -> str:
        """Generate error response"""
        return f"""## ROOT CAUSE
LLM analysis failed with error: {error}

## EVIDENCE
Unable to analyze due to API error.

## AFFECTED CODE
See source mapping section.

## FIX RECOMMENDATION
1. Check LLM API configuration
2. Verify network connectivity
3. Review API rate limits

## CONFIDENCE
0%

## PREVENTIVE MEASURES
- Monitor LLM API availability
- Implement retry logic
- Add fallback analysis options
"""
    
    def analyze_with_context(
        self,
        defect_info: str,
        dlt_logs: str,
        source_code: str = None,
        historical: str = None
    ) -> str:
        """
        Run analysis with full context
        
        Args:
            defect_info: Defect summary and description
            dlt_logs: DLT log excerpts
            source_code: Relevant source code (optional)
            historical: Similar historical defects (optional)
            
        Returns:
            LLM analysis response
        """
        prompt_parts = []
        
        prompt_parts.append("## DEFECT INFORMATION")
        prompt_parts.append(defect_info)
        prompt_parts.append("")
        
        prompt_parts.append("## DLT LOG ANALYSIS")
        prompt_parts.append(dlt_logs)
        prompt_parts.append("")
        
        if source_code:
            prompt_parts.append("## RELEVANT SOURCE CODE")
            prompt_parts.append(source_code)
            prompt_parts.append("")
        
        if historical:
            prompt_parts.append("## SIMILAR HISTORICAL DEFECTS")
            prompt_parts.append(historical)
            prompt_parts.append("")
        
        prompt_parts.append("## ANALYSIS REQUEST")
        prompt_parts.append("""
Please analyze the above information and provide:
1. ROOT CAUSE: What is the most likely root cause?
2. EVIDENCE: What evidence supports this conclusion?
3. AFFECTED CODE: Which source files need to be fixed?
4. FIX RECOMMENDATION: What specific code changes are needed?
5. CONFIDENCE: How confident are you (0-100%)?
6. PREVENTIVE MEASURES: How to prevent similar issues?
""")
        
        return self.analyze("\n".join(prompt_parts))
    
    def get_status(self) -> Dict[str, Any]:
        """Get LLM service status"""
        return {
            "provider": self.provider,
            "available": self.is_available(),
            "model": self.model,
            "endpoint": self.azure_endpoint or self.custom_endpoint or "openai.com"
        }
