#!/usr/bin/env python3
"""
JIRA Data Fetcher - Standalone utility for JIRA integration

Features:
- Fetch tickets by key or labels
- Download attachments (DLT files, logs, etc.) with chunked reading
- Update labels, add comments
- No external dependencies (uses Python standard library only)

Usage:
    # Fetch single ticket
    python jira_data_fetcher.py --ticket SAM1-11
    
    # Fetch by labels
    python jira_data_fetcher.py --labels needs-rca,auto-rca
    
    # Download attachments
    python jira_data_fetcher.py --ticket SAM1-11 --download-dir ./attachments
"""

import argparse
import base64
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib import error, parse, request

# Try to import official JIRA library
try:
    from jira import JIRA
    HAS_JIRA_LIB = True
except ImportError:
    HAS_JIRA_LIB = False

# Load .env file if it exists
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def normalize_base_url(base_url: str) -> str:
    """Normalize and validate JIRA base URL"""
    if not base_url:
        raise ValueError("Missing Jira base URL.")

    cleaned = base_url.strip()
    if cleaned.endswith('/'):
        cleaned = cleaned[:-1]

    parsed = parse.urlparse(cleaned)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid Jira base URL: {base_url}")

    return f"{parsed.scheme}://{parsed.netloc}"


def normalize_email(email: Optional[str]) -> str:
    """Normalize and validate JIRA email"""
    if not email:
        raise ValueError("Missing Jira email. Provide your Atlassian account email via --email or JIRA_EMAIL.")

    email = email.strip()
    if email.startswith(("http://", "https://")):
        raise ValueError(
            "The Jira email value looks like a URL. Provide your Atlassian account email address, not the Jira site URL."
        )
    return email


def build_auth_header(email: str, api_token: str) -> dict:
    """Build Basic Auth header for JIRA API"""
    credentials = f"{email}:{api_token}".encode("utf-8")
    encoded = base64.b64encode(credentials).decode("ascii")
    return {"Authorization": f"Basic {encoded}", "Accept": "application/json", "Content-Type": "application/json"}


def extract_description(description_field) -> str:
    """
    Convert Jira description field to a readable string.
    Jira Cloud often returns description as an Atlassian Document Format (ADF) dict:
    { "type": "doc", "version": 1, "content": [ ... ] }
    This helper walks the content and extracts plain text.
    If description_field is already a string, return it.
    """
    if description_field is None:
        return ""

    # If it's a plain string
    if isinstance(description_field, str):
        return description_field

    # If it's an ADF structure
    if isinstance(description_field, dict):
        parts = []

        def walk(node):
            if not node:
                return
            node_type = node.get("type")
            if node_type == "text":
                parts.append(node.get("text", ""))
            # Some nodes have 'content' which is a list of child nodes
            for child in node.get("content", []) or []:
                walk(child)

        walk(description_field)
        # Join with double newlines between block-level nodes if needed
        return "\n".join(p for p in (p.strip() for p in parts) if p)

    # Fallback: try to stringify
    try:
        return str(description_field)
    except Exception:
        return ""


class JiraDataFetcher:
    """
    JIRA Data Fetcher class for RCA automation
    
    Supports:
    - Connection testing
    - Fetch single ticket or by labels
    - Download attachments (with chunked reading for large files)
    - Update labels, add comments (for automation)
    """
    
    def __init__(self, base_url: str = None, email: str = None, api_token: str = None):
        """
        Initialize JIRA fetcher
        
        Args:
            base_url: JIRA base URL (or set JIRA_BASE_URL env var)
            email: JIRA email (or set JIRA_EMAIL env var)
            api_token: JIRA API token (or set JIRA_API_TOKEN env var)
        """
        self.base_url = normalize_base_url(
            base_url or os.getenv("JIRA_BASE_URL") or os.getenv("JIRA_URL")
        )
        self.email = normalize_email(
            email or os.getenv("JIRA_EMAIL") or os.getenv("JIRA_USERNAME")
        )
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN")
        
        if not self.api_token:
            raise ValueError("Missing Jira API token. Set JIRA_API_TOKEN or pass api_token.")
        
        self.headers = build_auth_header(self.email, self.api_token)
        self._connected = False
        self.jira_client = None
        
        # Try to use official JIRA library if available
        if HAS_JIRA_LIB:
            try:
                self.jira_client = JIRA(
                    server=self.base_url,
                    basic_auth=(self.email, self.api_token)
                )
            except Exception as e:
                print(f"⚠ JIRA library initialization failed, using urllib: {e}")
                self.jira_client = None
    
    def test_connection(self) -> bool:
        """Test connection to JIRA"""
        api_url = f"{self.base_url}/rest/api/3/myself"
        req = request.Request(api_url, headers=self.headers, method="GET")

        try:
            with request.urlopen(req, timeout=20) as response:
                payload = response.read().decode("utf-8")
                data = json.loads(payload)
                display_name = data.get("displayName") or data.get("name") or "N/A"
                email_addr = data.get("emailAddress") or "N/A"
                print(f"✓ Connected to Jira as: {display_name} ({email_addr})")
                self._connected = True
                return True
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            print(f"✗ Jira authentication failed: {exc.code} {body}")
            return False
        except Exception as exc:
            print(f"✗ Unable to connect to Jira: {exc}")
            return False
    
    def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a JIRA issue (alias for fetch_ticket for RCA engine compatibility)
        
        Args:
            issue_key: JIRA issue key (e.g., SAM1-11)
            
        Returns:
            Ticket data dict or None if failed
        """
        return self.fetch_ticket(issue_key, verbose=False)
    
    def fetch_ticket(self, ticket_key: str, verbose: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch a single JIRA ticket
        
        Args:
            ticket_key: JIRA issue key (e.g., SAM1-11)
            verbose: Print ticket details
            
        Returns:
            Ticket data dict or None if failed
        """
        api_url = f"{self.base_url}/rest/api/3/issue/{ticket_key}"
        req = request.Request(api_url, headers=self.headers, method="GET")

        try:
            with request.urlopen(req, timeout=20) as response:
                payload = response.read().decode("utf-8")
                data = json.loads(payload)
                
                if verbose:
                    print(f"Fetched ticket: {ticket_key}")
                    print(f"  Summary: {data.get('fields', {}).get('summary', 'N/A')}")
                    print(f"  Status: {data.get('fields', {}).get('status', {}).get('name', 'N/A')}")
                    print(f"  Issue Type: {data.get('fields', {}).get('issuetype', {}).get('name', 'N/A')}")

                # Normalize the data structure for RCA engine
                fields = data.get('fields', {})
                normalized = {
                    'key': data.get('key'),
                    'id': data.get('id'),
                    'summary': fields.get('summary', ''),
                    'description': extract_description(fields.get('description')),
                    'status': fields.get('status', {}).get('name', ''),
                    'issue_type': fields.get('issuetype', {}).get('name', ''),
                    'priority': fields.get('priority', {}).get('name', ''),
                    'labels': fields.get('labels', []),
                    'created': fields.get('created', ''),
                    'updated': fields.get('updated', ''),
                    'attachments': [],
                    '_raw': data  # Keep raw data for advanced use
                }
                
                # Normalize attachments
                for att in fields.get('attachment', []) or []:
                    normalized['attachments'].append({
                        'filename': att.get('filename', ''),
                        'content_url': att.get('content', ''),
                        'size': att.get('size', 0),
                        'mimeType': att.get('mimeType', ''),
                        'author': att.get('author', {}).get('displayName', '')
                    })
                
                return normalized
                
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            print(f"✗ Unable to fetch ticket {ticket_key}: {exc.code} {body}")
            return None
        except Exception as exc:
            print(f"✗ Unable to fetch ticket {ticket_key}: {exc}")
            return None
    
    def fetch_by_labels(self, labels: List[str], project_key: str = None,
                       additional_filter: str = None, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch tickets with specific labels
        
        Args:
            labels: List of labels to search for
            project_key: Optional project key filter
            additional_filter: Additional JQL filter
            max_results: Maximum results to return
            
        Returns:
            List of ticket data dicts
        """
        # Build JQL query
        label_conditions = " OR ".join([f'labels = "{label}"' for label in labels])
        jql = f"({label_conditions})"
        
        if project_key:
            jql = f"project = {project_key} AND {jql}"
        
        if additional_filter:
            jql = f"{jql} AND {additional_filter}"
        
        print(f"Searching JIRA: {jql}")
        
        # Use official JIRA library if available
        if self.jira_client:
            try:
                issues = self.jira_client.search_issues(
                    jql,
                    maxResults=max_results,
                    fields='key,summary,description,status,issuetype,priority,labels,created,updated,attachment'
                )
                tickets = []
                for issue in issues:
                    # Convert JIRA library issue to dict format
                    normalized = {
                        'key': issue.key,
                        'id': issue.id,
                        'summary': issue.fields.summary,
                        'description': getattr(issue.fields, 'description', ''),
                        'status': issue.fields.status.name if hasattr(issue.fields, 'status') else '',
                        'issue_type': issue.fields.issuetype.name if hasattr(issue.fields, 'issuetype') else '',
                        'priority': issue.fields.priority.name if hasattr(issue.fields, 'priority') and issue.fields.priority else '',
                        'labels': getattr(issue.fields, 'labels', []),
                        'created': getattr(issue.fields, 'created', ''),
                        'updated': getattr(issue.fields, 'updated', ''),
                        'attachments': [],
                        '_raw': issue.raw
                    }
                    # Handle ADF description format
                    if normalized['description'] and hasattr(normalized['description'], 'content'):
                        normalized['description'] = extract_description(normalized['description'])
                    
                    tickets.append(normalized)
                
                print(f"Found {len(tickets)} tickets with labels: {labels}")
                return tickets
            except Exception as e:
                print(f"✗ Search failed with JIRA library: {e}")
                return []
        
        # Fallback to urllib implementation
        # Use POST method with JSON body
        api_url = f"{self.base_url}/rest/api/3/search"
        body = json.dumps({
            'jql': jql,
            'maxResults': max_results,
            'fields': ['key', 'summary', 'description', 'status', 'issuetype', 'priority', 'labels', 'created', 'updated', 'attachment']
        }).encode('utf-8')
        
        req = request.Request(api_url, data=body, headers=self.headers, method="POST")
        
        try:
            with request.urlopen(req, timeout=30) as response:
                payload = response.read().decode("utf-8")
                data = json.loads(payload)
                
                tickets = []
                for issue in data.get('issues', []):
                    # Reuse fetch_ticket normalization by building minimal structure
                    normalized = self._normalize_issue(issue)
                    tickets.append(normalized)
                
                print(f"Found {len(tickets)} tickets with labels: {labels}")
                return tickets
                
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            print(f"✗ Search failed: {exc.code} {body}")
            return []
        except Exception as exc:
            print(f"✗ Search failed: {exc}")
            return []
    
    def _normalize_issue(self, issue: Dict) -> Dict[str, Any]:
        """Normalize issue data structure"""
        fields = issue.get('fields', {})
        normalized = {
            'key': issue.get('key'),
            'id': issue.get('id'),
            'summary': fields.get('summary', ''),
            'description': extract_description(fields.get('description')),
            'status': fields.get('status', {}).get('name', '') if fields.get('status') else '',
            'issue_type': fields.get('issuetype', {}).get('name', '') if fields.get('issuetype') else '',
            'priority': fields.get('priority', {}).get('name', '') if fields.get('priority') else '',
            'labels': fields.get('labels', []),
            'created': fields.get('created', ''),
            'updated': fields.get('updated', ''),
            'attachments': [],
            '_raw': issue
        }
        
        for att in fields.get('attachment', []) or []:
            normalized['attachments'].append({
                'filename': att.get('filename', ''),
                'content_url': att.get('content', ''),
                'size': att.get('size', 0),
                'mimeType': att.get('mimeType', ''),
                'author': att.get('author', {}).get('displayName', '')
            })
        
        return normalized
    
    def download_attachment(self, content_url: str, output_path: str) -> bool:
        """
        Download a single attachment with chunked reading
        
        Args:
            content_url: URL to download from
            output_path: Local file path to save to
            
        Returns:
            True if successful
        """
        if not content_url:
            return False
        
        # Handle relative URLs
        parsed = parse.urlparse(content_url)
        if not parsed.scheme:
            content_url = f"{self.base_url}{content_url if content_url.startswith('/') else '/' + content_url}"
        
        req = request.Request(content_url, headers=self.headers, method="GET")
        
        try:
            with request.urlopen(req, timeout=60) as resp:
                # Ensure directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Read in chunks to avoid memory spikes on large DLT files
                with open(output_path, "wb") as f:
                    chunk_size = 8192
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                
                print(f"  ✓ Downloaded: {os.path.basename(output_path)}")
                return True
                
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            print(f"  ✗ Download failed: HTTP {exc.code} {body}")
            return False
        except Exception as exc:
            print(f"  ✗ Download failed: {exc}")
            return False
    
    def download_attachments(self, ticket_key: str, dest_dir: str, 
                            filter_extensions: List[str] = None) -> List[str]:
        """
        Download all attachments from a ticket
        
        Args:
            ticket_key: JIRA issue key
            dest_dir: Destination directory
            filter_extensions: Optional list of extensions to filter (e.g., ['.dlt', '.log'])
            
        Returns:
            List of downloaded file paths
        """
        ticket = self.fetch_ticket(ticket_key, verbose=False)
        if not ticket:
            return []
        
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True)
        
        downloaded = []
        attachments = ticket.get('attachments', [])
        
        if not attachments:
            print(f"No attachments found on {ticket_key}")
            return []
        
        print(f"Downloading {len(attachments)} attachment(s) from {ticket_key}...")
        
        for att in attachments:
            filename = att.get('filename', '')
            content_url = att.get('content_url', '')
            
            if not filename or not content_url:
                continue
            
            # Filter by extension if specified
            if filter_extensions:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in filter_extensions:
                    continue
            
            # Handle duplicate filenames
            out_file = dest_path / filename
            if out_file.exists():
                base, ext = os.path.splitext(filename)
                i = 1
                while True:
                    candidate = dest_path / f"{base}_{i}{ext}"
                    if not candidate.exists():
                        out_file = candidate
                        break
                    i += 1
            
            if self.download_attachment(content_url, str(out_file)):
                downloaded.append(str(out_file))
        
        return downloaded
    
    def download_dlt_attachments(self, ticket_key: str, dest_dir: str = "data/dlt_logs") -> List[str]:
        """Download only DLT and log files from a ticket"""
        return self.download_attachments(
            ticket_key, 
            dest_dir, 
            filter_extensions=['.dlt', '.log', '.txt']
        )
    
    def download_ticket_attachments_to_workspace(self, ticket: Dict[str, Any], workspace_dir: str) -> List[str]:
        """
        Download attachments from an already-fetched ticket to a workspace folder
        
        This is optimized for the scheduler - no extra API call needed.
        All files are downloaded directly to the workspace folder.
        
        Args:
            ticket: Already fetched ticket data dict
            workspace_dir: Directory to download to (all files go here)
            
        Returns:
            List of downloaded file paths
        """
        downloaded = []
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Get attachments from ticket (check both locations)
        attachments = ticket.get('attachments', [])
        if not attachments:
            # Try getting from fields (standard JIRA API response structure)
            fields = ticket.get('fields', {})
            attachments = fields.get('attachment', [])
        
        if not attachments:
            # Also check raw data
            raw = ticket.get('_raw', {})
            if raw:
                raw_fields = raw.get('fields', {})
                attachments = raw_fields.get('attachment', [])
        
        if not attachments:
            print(f"   ℹ️ No attachments found in ticket {ticket.get('key', 'unknown')}")
            print(f"      Checked: ticket['attachments'], ticket['fields']['attachment'], ticket['_raw']['fields']['attachment']")
            return []
        
        ticket_key = ticket.get('key', 'unknown')
        print(f"📥 Downloading {len(attachments)} attachment(s) from {ticket_key}...")
        
        for att in attachments:
            filename = att.get('filename', '')
            # Try both 'content_url' (normalized) and 'content' (raw JIRA API)
            content_url = att.get('content_url') or att.get('content', '')
            
            if not filename or not content_url:
                continue
            
            # All files go to workspace root
            out_file = Path(workspace_dir) / filename
            
            # Handle duplicate filenames
            if out_file.exists():
                base, ext = os.path.splitext(filename)
                i = 1
                while True:
                    candidate = Path(workspace_dir) / f"{base}_{i}{ext}"
                    if not candidate.exists():
                        out_file = candidate
                        break
                    i += 1
            
            if self.download_attachment(content_url, str(out_file)):
                downloaded.append(str(out_file))
        
        return downloaded
    
    # ==========================================
    # WRITE OPERATIONS (for automation)
    # ==========================================
    
    def update_labels(self, ticket_key: str, add_labels: List[str] = None,
                     remove_labels: List[str] = None) -> bool:
        """
        Update labels on a JIRA ticket
        
        Args:
            ticket_key: JIRA issue key
            add_labels: Labels to add
            remove_labels: Labels to remove
            
        Returns:
            True if successful
        """
        update_data = {"update": {"labels": []}}
        
        if add_labels:
            for label in add_labels:
                update_data["update"]["labels"].append({"add": label})
        
        if remove_labels:
            for label in remove_labels:
                update_data["update"]["labels"].append({"remove": label})
        
        if not update_data["update"]["labels"]:
            return True  # Nothing to do
        
        api_url = f"{self.base_url}/rest/api/3/issue/{ticket_key}"
        data = json.dumps(update_data).encode('utf-8')
        req = request.Request(api_url, data=data, headers=self.headers, method="PUT")
        
        try:
            with request.urlopen(req, timeout=20) as response:
                print(f"  ✓ Updated labels on {ticket_key}")
                return True
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            print(f"  ✗ Failed to update labels on {ticket_key}: {exc.code} {body}")
            return False
        except Exception as exc:
            print(f"  ✗ Failed to update labels on {ticket_key}: {exc}")
            return False
    
    def add_comment(self, ticket_key: str, comment_text: str) -> bool:
        """
        Add a comment to a JIRA ticket
        
        Args:
            ticket_key: JIRA issue key
            comment_text: Comment text (plain text, will be converted to ADF)
            
        Returns:
            True if successful
        """
        # Convert plain text to Atlassian Document Format (ADF)
        # Split text into paragraphs
        paragraphs = comment_text.split('\n')
        content = []
        
        for para in paragraphs:
            if para.strip():
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": para}]
                })
            else:
                # Empty line = blank paragraph
                content.append({
                    "type": "paragraph",
                    "content": []
                })
        
        comment_data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": content
            }
        }
        
        api_url = f"{self.base_url}/rest/api/3/issue/{ticket_key}/comment"
        data = json.dumps(comment_data).encode('utf-8')
        req = request.Request(api_url, data=data, headers=self.headers, method="POST")
        
        try:
            with request.urlopen(req, timeout=20) as response:
                print(f"  ✓ Added comment to {ticket_key}")
                return True
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            print(f"  ✗ Failed to add comment to {ticket_key}: {exc.code} {body}")
            return False
        except Exception as exc:
            print(f"  ✗ Failed to add comment to {ticket_key}: {exc}")
            return False
    
    def add_attachment(self, ticket_key: str, file_path: str) -> bool:
        """
        Upload attachment to a JIRA ticket
        
        Args:
            ticket_key: JIRA issue key
            file_path: Path to file to upload
            
        Returns:
            True if successful
        """
        if not os.path.exists(file_path):
            print(f"  ✗ File not found: {file_path}")
            return False
        
        try:
            import mimetypes
            
            # Prepare multipart/form-data upload
            filename = os.path.basename(file_path)
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Guess MIME type
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Generate boundary for multipart/form-data
            import random
            import string
            boundary = ''.join(random.choices(string.ascii_letters + string.digits, k=30))
            
            # Build multipart body
            body_parts = []
            body_parts.append(f'--{boundary}'.encode())
            body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode())
            body_parts.append(f'Content-Type: {mime_type}'.encode())
            body_parts.append(b'')
            body_parts.append(file_content)
            body_parts.append(f'--{boundary}--'.encode())
            
            body = b'\r\n'.join(body_parts)
            
            # Prepare request
            api_url = f"{self.base_url}/rest/api/3/issue/{ticket_key}/attachments"
            
            # Custom headers for file upload
            upload_headers = {
                **self.headers,
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'X-Atlassian-Token': 'no-check'  # Required for JIRA attachments
            }
            # Remove conflicting Content-Type from base headers
            if 'Content-Type' in self.headers:
                upload_headers = {k: v for k, v in self.headers.items() if k != 'Content-Type'}
                upload_headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
                upload_headers['X-Atlassian-Token'] = 'no-check'
                upload_headers['Authorization'] = self.headers['Authorization']
                upload_headers['Accept'] = 'application/json'
            
            req = request.Request(api_url, data=body, headers=upload_headers, method="POST")
            
            with request.urlopen(req, timeout=60) as response:
                print(f"  ✓ Uploaded {filename} to {ticket_key}")
                return True
                
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            print(f"  ✗ Failed to upload {filename} to {ticket_key}: {exc.code} {body}")
            return False
        except Exception as exc:
            print(f"  ✗ Failed to upload attachment to {ticket_key}: {exc}")
            return False
    
    def link_duplicate(self, issue_key: str, duplicate_of: str) -> bool:
        """
        Link an issue as duplicate of another issue
        
        Args:
            issue_key: The duplicate issue key
            duplicate_of: The original issue key
            
        Returns:
            True if successful
        """
        try:
            api_url = f"{self.base_url}/rest/api/3/issueLink"
            
            link_data = {
                "type": {
                    "name": "Duplicate"
                },
                "inwardIssue": {
                    "key": issue_key
                },
                "outwardIssue": {
                    "key": duplicate_of
                },
                "comment": {
                    "body": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Automatically detected as duplicate by RCA Agent"
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
            
            data = json.dumps(link_data).encode('utf-8')
            req = request.Request(api_url, data=data, headers=self.headers, method="POST")
            
            with request.urlopen(req, timeout=20) as response:
                print(f"  ✓ Linked {issue_key} as duplicate of {duplicate_of}")
                return True
                
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            print(f"  ✗ Failed to link {issue_key} as duplicate: {exc.code} {body}")
            return False
        except Exception as exc:
            print(f"  ✗ Failed to link duplicate: {exc}")
            return False
    
    def save_ticket_metadata(self, ticket_key: str, dest_dir: str) -> str:
        """
        Save ticket metadata JSON alongside downloaded attachments
        
        Args:
            ticket_key: JIRA issue key
            dest_dir: Destination directory
            
        Returns:
            Path to metadata file
        """
        ticket = self.fetch_ticket(ticket_key, verbose=False)
        if not ticket:
            return ""
        
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True)
        
        meta = {
            "key": ticket.get('key'),
            "summary": ticket.get('summary'),
            "description": ticket.get('description'),
            "status": ticket.get('status'),
            "labels": ticket.get('labels'),
            "attachments": ticket.get('attachments', [])
        }
        
        meta_file = dest_path / f"{ticket_key}_metadata.json"
        try:
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            print(f"Saved ticket metadata to: {meta_file}")
            return str(meta_file)
        except Exception as exc:
            print(f"Failed to save metadata file: {exc}")
            return ""


# ==========================================
# STANDALONE FUNCTIONS (for CLI use)
# ==========================================

def connect_to_jira(base_url: str, email: str, api_token: str) -> bool:
    """Standalone connection test"""
    fetcher = JiraDataFetcher(base_url, email, api_token)
    return fetcher.test_connection()


def fetch_ticket(base_url: str, ticket_key: str, email: str, api_token: str) -> dict:
    """Standalone fetch ticket"""
    fetcher = JiraDataFetcher(base_url, email, api_token)
    return fetcher.fetch_ticket(ticket_key)


def download_attachments(ticket_data: dict, base_url: str, email: str, 
                        api_token: str, dest_dir: str) -> List[str]:
    """Standalone download attachments"""
    fetcher = JiraDataFetcher(base_url, email, api_token)
    ticket_key = ticket_data.get('key')
    if ticket_key:
        return fetcher.download_attachments(ticket_key, dest_dir)
    return []


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Connect to Jira, fetch tickets, download attachments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch single ticket
  python jira_data_fetcher.py --ticket SAM1-11

  # Fetch by labels
  python jira_data_fetcher.py --labels needs-rca,auto-rca

  # Download attachments
  python jira_data_fetcher.py --ticket SAM1-11 --download-dir ./attachments

  # Save metadata
  python jira_data_fetcher.py --ticket SAM1-11 --save-metadata
        """
    )
    parser.add_argument("--base-url", default=os.getenv("JIRA_BASE_URL", "https://hrishabhtiwari.atlassian.net"))
    parser.add_argument("--ticket", default=os.getenv("JIRA_TICKET_KEY"))
    parser.add_argument("--labels", help="Comma-separated labels to search")
    parser.add_argument("--project", help="Project key filter")
    parser.add_argument("--email", default=os.getenv("JIRA_EMAIL"))
    parser.add_argument("--username", default=os.getenv("JIRA_USERNAME"))
    parser.add_argument("--api-token", default=os.getenv("JIRA_API_TOKEN"))
    parser.add_argument("--download-dir", default=os.getenv("JIRA_DOWNLOAD_DIR", "./attachments"))
    parser.add_argument("--save-metadata", action="store_true", help="Save ticket metadata JSON")
    parser.add_argument("--dlt-only", action="store_true", help="Download only DLT/log files")
    args = parser.parse_args()

    if not args.api_token:
        raise SystemExit("Missing Jira API token. Set JIRA_API_TOKEN or pass --api-token.")

    try:
        fetcher = JiraDataFetcher(
            base_url=args.base_url,
            email=args.email or args.username,
            api_token=args.api_token
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    # Test connection
    if not fetcher.test_connection():
        raise SystemExit("Failed to connect to JIRA")
    
    # Fetch by labels
    if args.labels:
        labels = [l.strip() for l in args.labels.split(',')]
        tickets = fetcher.fetch_by_labels(labels, project_key=args.project)
        
        for ticket in tickets:
            print(f"\n{ticket['key']}: {ticket['summary']}")
            
            if args.download_dir:
                ticket_dir = os.path.join(args.download_dir, ticket['key'])
                if args.dlt_only:
                    fetcher.download_dlt_attachments(ticket['key'], ticket_dir)
                else:
                    fetcher.download_attachments(ticket['key'], ticket_dir)
                
                if args.save_metadata:
                    fetcher.save_ticket_metadata(ticket['key'], ticket_dir)
    
    # Fetch single ticket
    elif args.ticket:
        ticket = fetcher.fetch_ticket(args.ticket)
        
        if ticket and args.download_dir:
            if args.dlt_only:
                fetcher.download_dlt_attachments(args.ticket, args.download_dir)
            else:
                fetcher.download_attachments(args.ticket, args.download_dir)
            
            if args.save_metadata:
                fetcher.save_ticket_metadata(args.ticket, args.download_dir)
    
    else:
        print("Specify --ticket or --labels to fetch tickets")


if __name__ == "__main__":
    main()
