"""
JIRA Service - Integration with JIRA for defect management

PLACEHOLDER: This module contains placeholder methods for JIRA API integration.
The actual implementation will use your organization's JIRA API credentials.

Features:
- Fetch defect details
- Add comments with RCA results
- Upload attachments (MD, HTML reports)
- Link duplicate defects
- Update defect status/fields
"""

import os
import logging
from typing import Dict, Any, List, Optional
import requests
from requests.auth import HTTPBasicAuth


class JiraService:
    """
    JIRA Integration Service
    
    PLACEHOLDER: Configure with your JIRA credentials:
    - JIRA_URL: Your JIRA instance URL
    - JIRA_EMAIL: Your Atlassian account email
    - JIRA_API_TOKEN: Your JIRA API token
    
    All methods are implemented with placeholder logic that can be
    replaced with actual JIRA API calls once credentials are provided.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize JIRA Service
        
        Args:
            config: Configuration dictionary with JIRA settings
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # JIRA Configuration - PLACEHOLDER
        jira_config = config.get('jira', {})
        
        self.jira_url = jira_config.get('url') or os.getenv('JIRA_URL', '')
        self.jira_email = jira_config.get('email') or os.getenv('JIRA_EMAIL', '')
        self.jira_token = jira_config.get('api_token') or os.getenv('JIRA_API_TOKEN', '')
        self.project_key = jira_config.get('project_key') or os.getenv('JIRA_PROJECT_KEY', '')
        
        self.connected = False
        self._client = None
        
        # Validate configuration
        if self.jira_url and self.jira_email and self.jira_token:
            self._init_client()
    
    def _init_client(self):
        """Initialize JIRA REST API client"""
        try:
            self.auth = HTTPBasicAuth(self.jira_email, self.jira_token)
            self.headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            self.connected = True
            self.logger.info(f"JIRA client initialized for {self.jira_url}")
        except Exception as e:
            self.logger.error(f"Failed to initialize JIRA client: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if JIRA is configured and connected"""
        return self.connected
    
    # ==========================================
    # DEFECT OPERATIONS
    # ==========================================
    
    def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """
        Get defect details from JIRA
        
        PLACEHOLDER: Replace with actual JIRA API call
        
        Args:
            issue_key: JIRA issue key (e.g., SAM1-2001)
            
        Returns:
            Defect data dictionary
        """
        if not self.connected:
            self.logger.warning("JIRA not connected - returning placeholder data")
            return self._get_placeholder_issue(issue_key)
        
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}"
            response = requests.get(url, headers=self.headers, auth=self.auth)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_issue(data)
            
        except Exception as e:
            self.logger.error(f"Failed to get issue {issue_key}: {e}")
            return None
    
    def search_issues(self, jql: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search JIRA issues using JQL
        
        PLACEHOLDER: Replace with actual JIRA API call
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results
            
        Returns:
            List of matching issues
        """
        if not self.connected:
            self.logger.warning("JIRA not connected")
            return []
        
        try:
            url = f"{self.jira_url}/rest/api/3/search"
            params = {
                'jql': jql,
                'maxResults': max_results,
                'fields': 'summary,status,priority,assignee,reporter,description,created,updated,components,labels'
            }
            
            response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
            response.raise_for_status()
            
            data = response.json()
            return [self._parse_issue(issue) for issue in data.get('issues', [])]
            
        except Exception as e:
            self.logger.error(f"Failed to search issues: {e}")
            return []
    
    # ==========================================
    # COMMENT OPERATIONS
    # ==========================================
    
    def add_comment(self, issue_key: str, comment: str) -> bool:
        """
        Add RCA comment to JIRA issue
        
        PLACEHOLDER: Replace with actual JIRA API call
        
        Args:
            issue_key: JIRA issue key
            comment: Comment text (JIRA wiki markup)
            
        Returns:
            Success status
        """
        if not self.connected:
            self.logger.warning(f"JIRA not connected - comment for {issue_key} not posted")
            self.logger.info(f"Comment preview:\n{comment[:200]}...")
            return False
        
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}/comment"
            
            # JIRA API v3 uses Atlassian Document Format
            payload = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment
                                }
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
            response.raise_for_status()
            
            self.logger.info(f"Added comment to {issue_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add comment to {issue_key}: {e}")
            return False
    
    # ==========================================
    # ATTACHMENT OPERATIONS
    # ==========================================
    
    def add_attachment(self, issue_key: str, file_path: str) -> bool:
        """
        Upload attachment (MD/HTML report) to JIRA issue
        
        PLACEHOLDER: Replace with actual JIRA API call
        
        Args:
            issue_key: JIRA issue key
            file_path: Path to the file to upload
            
        Returns:
            Success status
        """
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return False
        
        if not self.connected:
            self.logger.warning(f"JIRA not connected - attachment {file_path} not uploaded to {issue_key}")
            return False
        
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}/attachments"
            
            # For file upload, use different headers
            headers = {
                "Accept": "application/json",
                "X-Atlassian-Token": "no-check"
            }
            
            filename = os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f)}
                response = requests.post(url, headers=headers, auth=self.auth, files=files)
                response.raise_for_status()
            
            self.logger.info(f"Uploaded {filename} to {issue_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload attachment to {issue_key}: {e}")
            return False
    
    def upload_reports(
        self, 
        issue_key: str, 
        md_path: str, 
        html_path: str
    ) -> Dict[str, bool]:
        """
        Upload both MD and HTML reports to JIRA
        
        Args:
            issue_key: JIRA issue key
            md_path: Path to Markdown report
            html_path: Path to HTML report
            
        Returns:
            Dictionary with upload status for each file
        """
        result = {
            "markdown": self.add_attachment(issue_key, md_path),
            "html": self.add_attachment(issue_key, html_path)
        }
        return result
    
    # ==========================================
    # DUPLICATE LINKING
    # ==========================================
    
    def link_duplicate(
        self, 
        issue_key: str, 
        duplicate_of: str
    ) -> bool:
        """
        Link issue as duplicate of another issue
        
        PLACEHOLDER: Replace with actual JIRA API call
        
        Args:
            issue_key: The duplicate issue key
            duplicate_of: The original issue key
            
        Returns:
            Success status
        """
        if not self.connected:
            self.logger.warning(
                f"JIRA not connected - cannot link {issue_key} as duplicate of {duplicate_of}"
            )
            return False
        
        try:
            url = f"{self.jira_url}/rest/api/3/issueLink"
            
            payload = {
                "type": {
                    "name": "Duplicate"
                },
                "inwardIssue": {
                    "key": issue_key
                },
                "outwardIssue": {
                    "key": duplicate_of
                }
            }
            
            response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
            response.raise_for_status()
            
            self.logger.info(f"Linked {issue_key} as duplicate of {duplicate_of}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to link duplicate: {e}")
            return False
    
    def add_duplicate_comment(
        self, 
        issue_key: str, 
        duplicate_of: str, 
        similarity: float
    ) -> bool:
        """
        Add comment indicating potential duplicate
        
        Args:
            issue_key: JIRA issue key
            duplicate_of: Original defect key
            similarity: Similarity score (0-1)
            
        Returns:
            Success status
        """
        comment = f"""
h2. ⚠️ Potential Duplicate Detected

This defect is *{similarity:.0%}* similar to *{duplicate_of}*.

*Actions Required:*
# Review {duplicate_of} to confirm duplicate relationship
# If confirmed, link this issue as "Duplicates" {duplicate_of}
# Close this issue as duplicate if appropriate

_Detected by RCA Agent_
"""
        return self.add_comment(issue_key, comment)
    
    # ==========================================
    # UPDATE OPERATIONS
    # ==========================================
    
    def update_issue(
        self, 
        issue_key: str, 
        fields: Dict[str, Any]
    ) -> bool:
        """
        Update JIRA issue fields
        
        PLACEHOLDER: Replace with actual JIRA API call
        
        Args:
            issue_key: JIRA issue key
            fields: Dictionary of fields to update
            
        Returns:
            Success status
        """
        if not self.connected:
            self.logger.warning(f"JIRA not connected - cannot update {issue_key}")
            return False
        
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}"
            
            payload = {"fields": fields}
            
            response = requests.put(url, headers=self.headers, auth=self.auth, json=payload)
            response.raise_for_status()
            
            self.logger.info(f"Updated {issue_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update {issue_key}: {e}")
            return False
    
    def assign_issue(self, issue_key: str, assignee: str) -> bool:
        """
        Assign issue to a user
        
        Args:
            issue_key: JIRA issue key
            assignee: Account ID or email of assignee
            
        Returns:
            Success status
        """
        return self.update_issue(issue_key, {"assignee": {"accountId": assignee}})
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def _parse_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JIRA API response into simplified format"""
        fields = data.get('fields', {})
        
        return {
            "key": data.get('key'),
            "summary": fields.get('summary', ''),
            "description": self._parse_adf_content(fields.get('description')),
            "status": fields.get('status', {}).get('name', ''),
            "priority": fields.get('priority', {}).get('name', ''),
            "assignee": fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
            "reporter": fields.get('reporter', {}).get('displayName') if fields.get('reporter') else None,
            "created": fields.get('created'),
            "updated": fields.get('updated'),
            "component": self._get_first_component(fields.get('components', [])),
            "labels": fields.get('labels', [])
        }
    
    def _parse_adf_content(self, adf: Optional[Dict]) -> str:
        """Parse Atlassian Document Format to plain text"""
        if not adf:
            return ""
        
        if isinstance(adf, str):
            return adf
        
        def extract_text(node):
            if isinstance(node, dict):
                if node.get('type') == 'text':
                    return node.get('text', '')
                text_parts = []
                for child in node.get('content', []):
                    text_parts.append(extract_text(child))
                return ' '.join(text_parts)
            return ''
        
        return extract_text(adf)
    
    def _get_first_component(self, components: List[Dict]) -> str:
        """Get first component name"""
        if components and len(components) > 0:
            return components[0].get('name', 'Unknown')
        return 'Unknown'
    
    def _get_placeholder_issue(self, issue_key: str) -> Dict[str, Any]:
        """Return placeholder issue data when JIRA is not connected"""
        return {
            "key": issue_key,
            "summary": f"Placeholder issue for {issue_key}",
            "description": "JIRA not connected - using placeholder data",
            "status": "Open",
            "priority": "Medium",
            "assignee": None,
            "reporter": None,
            "created": None,
            "updated": None,
            "component": "Unknown",
            "labels": []
        }
