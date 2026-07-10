"""
Git Service - Integration with Git repositories for source code access

PLACEHOLDER: This module contains placeholder methods for Git repository integration.
The actual implementation will use your organization's Git repository.

Features:
- Clone/pull source code repositories
- Access source files for RCA mapping
- Search code for patterns
- Get file history and blame information
- Create branches and Pull Requests for fixes
"""

import os
import logging
import re
import json
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


class GitService:
    """
    Git Repository Integration Service
    
    PLACEHOLDER: Configure with your Git repository settings:
    - GIT_REPO_URL: Repository URL (HTTPS or SSH)
    - GIT_BRANCH: Branch to use (default: main)
    - GIT_TOKEN: Personal access token for private repos
    - GIT_LOCAL_PATH: Local path to clone/store repo
    
    All methods are implemented with placeholder logic that can be
    replaced with actual Git operations once configured.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Git Service
        
        Args:
            config: Configuration dictionary with Git settings
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Git Configuration - PLACEHOLDER
        git_config = config.get('git', {})
        
        self.repo_url = git_config.get('repo_url') or os.getenv('GIT_REPO_URL', '')
        self.branch = git_config.get('branch') or os.getenv('GIT_BRANCH', 'main')
        self.token = git_config.get('token') or os.getenv('GIT_TOKEN', '')
        self.local_path = git_config.get('local_path') or os.getenv('GIT_LOCAL_PATH', 'data/source_repo')
        self.src_subdir = git_config.get('src_subdir', 'src')  # Subdirectory containing source code
        
       #enter prises login
        self.git_username = git_config.get('username') or os.getenv('GIT_USERNAME', '')
        self.github_enterprise_url = git_config.get('enterprise_api_url') or os.getenv('GITHUB_ENTERPRISE_API_URL', 'https://cc-github.bmwgroup.net/api/v3')
        
        self._repo = None
        self.connected = False
        
        # Try to initialize if configured
        if self.repo_url or os.path.exists(self.local_path):
            self._init_repo()
    
    def _init_repo(self):
        """Initialize Git repository connection"""
        try:
            # Check if local path exists (already cloned)
            if os.path.exists(os.path.join(self.local_path, '.git')):
                self.connected = True
                self.logger.info(f"Git repo found at {self.local_path}")
                return
            
            # Try to use GitPython if available
            try:
                import git
                if self.repo_url:
                    self.logger.info(f"Git configured for: {self.repo_url}")
                    self.connected = True
            except ImportError:
                self.logger.warning("GitPython not installed. Run: pip install GitPython")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Git: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if Git is configured and connected"""
        return self.connected
    
    # ==========================================
    # REPOSITORY OPERATIONS
    # ==========================================
    
    def clone_repo(self, force: bool = False) -> bool:
        """
        Clone the source code repository
        
        PLACEHOLDER: Replace with actual Git clone
        
        Args:
            force: If True, remove existing and re-clone
            
        Returns:
            Success status
        """
        if not self.repo_url:
            self.logger.warning("Git repo URL not configured")
            return False
        
        if os.path.exists(self.local_path) and not force:
            self.logger.info(f"Repo already exists at {self.local_path}")
            return True
        
        try:
            import git
            
            # Build clone URL with token if provided
            clone_url = self.repo_url
            if self.token and 'https://' in clone_url:
                # Insert token into URL
                clone_url = clone_url.replace('https://', f'https://{self.token}@')
            
            self.logger.info(f"Cloning repository to {self.local_path}...")
            git.Repo.clone_from(clone_url, self.local_path, branch=self.branch)
            
            self.connected = True
            self.logger.info("Repository cloned successfully")
            return True
            
        except ImportError:
            self.logger.error("GitPython not installed")
            return False
        except Exception as e:
            self.logger.error(f"Failed to clone repository: {e}")
            return False
    
    def pull_latest(self) -> bool:
        """
        Pull latest changes from remote
        
        PLACEHOLDER: Replace with actual Git pull
        
        Returns:
            Success status
        """
        if not self.connected:
            self.logger.warning("Git not connected")
            return False
        
        try:
            import git
            
            repo = git.Repo(self.local_path)
            origin = repo.remotes.origin
            origin.pull()
            
            self.logger.info("Pulled latest changes")
            return True
            
        except Exception as e:
            self.logger.warning("check pull: fallback to existing source repo.")
            return False
    
    # ==========================================
    # SOURCE CODE ACCESS
    # ==========================================
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        Get content of a source file
        
        Args:
            file_path: Relative path to file (e.g., "audio/AudioMixer.cpp")
            
        Returns:
            File content or None if not found
        """
        # Build full path
        full_path = os.path.join(self.local_path, self.src_subdir, file_path)
        
        # Also try without src_subdir
        if not os.path.exists(full_path):
            full_path = os.path.join(self.local_path, file_path)
        
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"Error reading {full_path}: {e}")
        
        self.logger.warning(f"File not found: {file_path}")
        return None
    
    def list_files(self, directory: str = "", extension: str = None) -> List[str]:
        """
        List files in repository
        
        Args:
            directory: Subdirectory to list (relative to src)
            extension: Filter by extension (e.g., ".cpp")
            
        Returns:
            List of file paths
        """
        base_path = os.path.join(self.local_path, self.src_subdir, directory)
        
        if not os.path.exists(base_path):
            base_path = os.path.join(self.local_path, directory)
        
        if not os.path.exists(base_path):
            return []
        
        files = []
        for root, dirs, filenames in os.walk(base_path):
            for filename in filenames:
                if extension is None or filename.endswith(extension):
                    rel_path = os.path.relpath(os.path.join(root, filename), self.local_path)
                    files.append(rel_path)
        
        return files
    
    def search_in_files(
        self, 
        pattern: str, 
        file_extension: str = ".cpp",
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for pattern in source files
        
        Args:
            pattern: Text pattern to search for
            file_extension: File extension to search
            max_results: Maximum number of results
            
        Returns:
            List of matches with file, line, and content
        """
        import re
        
        results = []
        files = self.list_files(extension=file_extension)
        
        for file_path in files:
            content = self.get_file_content(file_path)
            if not content:
                continue
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if re.search(pattern, line, re.IGNORECASE):
                    results.append({
                        "file": file_path,
                        "line": i + 1,
                        "content": line.strip()[:200]
                    })
                    
                    if len(results) >= max_results:
                        return results
        
        return results
    
    def get_file_context(
        self, 
        file_path: str, 
        line_number: int, 
        context_lines: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Get code context around a specific line
        
        Args:
            file_path: Path to source file
            line_number: Center line number
            context_lines: Lines of context before/after
            
        Returns:
            Context dictionary with code snippet
        """
        content = self.get_file_content(file_path)
        if not content:
            return None
        
        lines = content.split('\n')
        total_lines = len(lines)
        
        start = max(0, line_number - context_lines - 1)
        end = min(total_lines, line_number + context_lines)
        
        return {
            "file": file_path,
            "start_line": start + 1,
            "end_line": end,
            "center_line": line_number,
            "total_lines": total_lines,
            "code": '\n'.join(lines[start:end])
        }
    
    # ==========================================
    # GIT ANALYSIS
    # ==========================================
    
    def get_file_blame(self, file_path: str, line_number: int = None) -> Optional[Dict[str, Any]]:
        """
        Get blame information for a file
        
        PLACEHOLDER: Replace with actual Git blame
        
        Args:
            file_path: Path to file
            line_number: Specific line to blame (optional)
            
        Returns:
            Blame information
        """
        if not self.connected:
            return None
        
        try:
            import git
            
            repo = git.Repo(self.local_path)
            full_path = os.path.join(self.src_subdir, file_path)
            
            blame_data = repo.blame('HEAD', full_path)
            
            blame_info = []
            current_line = 1
            
            for commit, lines in blame_data:
                for line in lines:
                    info = {
                        "line": current_line,
                        "commit": commit.hexsha[:8],
                        "author": commit.author.name,
                        "date": commit.committed_datetime.isoformat(),
                        "message": commit.message.split('\n')[0][:50]
                    }
                    
                    if line_number is None or current_line == line_number:
                        blame_info.append(info)
                    
                    current_line += 1
            
            return {"file": file_path, "blame": blame_info}
            
        except Exception as e:
            self.logger.error(f"Failed to get blame: {e}")
            return None
    
    def get_recent_changes(
        self, 
        file_path: str = None, 
        days: int = 30,
        max_commits: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent changes/commits
        
        PLACEHOLDER: Replace with actual Git log
        
        Args:
            file_path: Filter by file path (optional)
            days: Number of days to look back
            max_commits: Maximum commits to return
            
        Returns:
            List of commit information
        """
        if not self.connected:
            return []
        
        try:
            import git
            from datetime import datetime, timedelta
            
            repo = git.Repo(self.local_path)
            since = datetime.now() - timedelta(days=days)
            
            commits = []
            for commit in repo.iter_commits(max_count=max_commits, since=since):
                commit_info = {
                    "hash": commit.hexsha[:8],
                    "author": commit.author.name,
                    "date": commit.committed_datetime.isoformat(),
                    "message": commit.message.strip()[:100]
                }
                
                if file_path:
                    # Check if file was modified in this commit
                    if file_path in [d.a_path for d in commit.diff(commit.parents[0] if commit.parents else None)]:
                        commits.append(commit_info)
                else:
                    commits.append(commit_info)
            
            return commits
            
        except Exception as e:
            self.logger.error(f"Failed to get commits: {e}")
            return []
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get Git service status"""
        return {
            "connected": self.connected,
            "repo_url": self.repo_url or "Not configured",
            "branch": self.branch,
            "local_path": self.local_path,
            "has_local_repo": os.path.exists(os.path.join(self.local_path, '.git'))
        }
    
    def find_related_files(self, component: str) -> List[str]:
        """
        Find files related to a component
        
        Args:
            component: Component name (e.g., "AudioMixer")
            
        Returns:
            List of related file paths
        """
        pattern = component.lower()
        files = self.list_files(extension=".cpp") + self.list_files(extension=".h")
        
        related = []
        for file_path in files:
            if pattern in file_path.lower():
                related.append(file_path)
        
        return related
    
    def get_source_for_mapping(self, mapped_files: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Get source code for mapped files
        
        Args:
            mapped_files: List of file mappings from SourceMapper
            
        Returns:
            Dictionary of file_path -> content
        """
        source_code = {}
        
        for file_info in mapped_files:
            file_path = file_info.get('file', '')
            content = self.get_file_content(file_path)
            
            if content:
                source_code[file_path] = content
            else:
                # Try alternate paths
                alt_paths = [
                    file_path,
                    f"src/{file_path}",
                    file_path.replace('/', '\\'),
                    os.path.basename(file_path)
                ]
                
                for alt_path in alt_paths:
                    content = self.get_file_content(alt_path)
                    if content:
                        source_code[file_path] = content
                        break
        
        return source_code

    # ==========================================
    # BRANCH & PR OPERATIONS
    # ==========================================
    
    def create_fix_branch(self, defect_id: str, base_branch: str = None) -> Optional[str]:
        """
        Create a new branch for the fix
        
        Args:
            defect_id: Defect/ticket ID (e.g., "SAM1-2001")
            base_branch: Base branch to create from (default: main)
            
        Returns:
            Branch name if successful, None otherwise
        """
        if not self.connected:
            self.logger.warning("Git not connected")
            return None
        
        try:
            import git
            
            repo = git.Repo(self.local_path)
            base = base_branch or self.branch
            
            # Generate branch name
            timestamp = datetime.now().strftime("%Y%m%d")
            branch_name = f"fix/{defect_id.lower()}-{timestamp}"
            
            # Check if branch already exists
            if branch_name in [b.name for b in repo.branches]:
                self.logger.info(f"Branch {branch_name} already exists, checking out")
                repo.git.checkout(branch_name)
                return branch_name
            
            # Checkout base and pull latest
            repo.git.checkout(base)
            try:
                repo.remotes.origin.pull()
            except Exception as e:
                self.logger.warning(f"Could not pull latest: {e}")
            
            # Create and checkout new branch
            repo.git.checkout('-b', branch_name)
            
            self.logger.info(f"Created branch: {branch_name}")
            return branch_name
            
        except ImportError:
            self.logger.error("GitPython not installed. Run: pip install GitPython")
            return None
        except Exception as e:
            self.logger.error(f"Failed to create branch: {e}")
            return None
    
    def apply_fix(
        self, 
        file_path: str, 
        old_content: str, 
        new_content: str
    ) -> bool:
        """
        Apply a fix to a source file (replace content)
        
        Args:
            file_path: Path to file (relative to repo)
            old_content: Content to find and replace
            new_content: New content to insert
            
        Returns:
            Success status
        """
        # Build full path
        full_path = os.path.join(self.local_path, self.src_subdir, file_path)
        
        if not os.path.exists(full_path):
            full_path = os.path.join(self.local_path, file_path)
        
        if not os.path.exists(full_path):
            self.logger.error(f"File not found: {file_path}")
            return False
        
        try:
            # Read current content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if old content exists
            if old_content not in content:
                self.logger.warning(f"Pattern not found in {file_path}")
                return False
            
            # Apply fix
            new_file_content = content.replace(old_content, new_content, 1)
            
            # Write back
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)
            
            self.logger.info(f"Applied fix to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply fix: {e}")
            return False
    
    def commit_fix(
        self, 
        defect_id: str, 
        message: str = None,
        files: List[str] = None
    ) -> Optional[str]:
        """
        Commit the fix changes
        
        Args:
            defect_id: Defect/ticket ID for commit message
            message: Custom commit message (optional)
            files: Specific files to commit (optional, default: all changes)
            
        Returns:
            Commit hash if successful, None otherwise
        """
        if not self.connected:
            self.logger.warning("Git not connected")
            return None
        
        try:
            import git
            
            repo = git.Repo(self.local_path)
            
            # Stage files
            if files:
                for file_path in files:
                    full_path = os.path.join(self.local_path, file_path)
                    if os.path.exists(full_path):
                        repo.index.add([file_path])
            else:
                # Stage all changes
                repo.git.add('-A')
            
            # Check if there are changes to commit
            if not repo.index.diff("HEAD"):
                self.logger.warning("No changes to commit")
                return None
            
            # Commit
            commit_message = message or f"fix({defect_id}): Apply RCA recommended fix\n\nAutomated fix based on Root Cause Analysis.\nDefect: {defect_id}"
            
            commit = repo.index.commit(commit_message)
            
            self.logger.info(f"Committed: {commit.hexsha[:8]}")
            return commit.hexsha
            
        except ImportError:
            self.logger.error("GitPython not installed")
            return None
        except Exception as e:
            self.logger.error(f"Failed to commit: {e}")
            return None
    
    def push_branch(self, branch_name: str = None) -> bool:
        """
        Push current branch to remote
        
        Args:
            branch_name: Branch to push (default: current branch)
            
        Returns:
            Success status
        """
        if not self.connected:
            self.logger.warning("Git not connected")
            return False
        
        try:
            import git
            
            repo = git.Repo(self.local_path)
            branch = branch_name or repo.active_branch.name
            
            # Push to origin
            origin = repo.remotes.origin
            push_info = origin.push(branch, set_upstream=True)
            
            self.logger.info(f"Pushed branch: {branch}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to push: {e}")
            return False
    
    def create_pull_request(
        self,
        defect_id: str,
        branch_name: str,
        title: str = None,
        description: str = None,
        base_branch: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Pull Request on GitHub/GitLab/Bitbucket
        
        Args:
            defect_id: Defect/ticket ID
            branch_name: Source branch for PR
            title: PR title (auto-generated if not provided)
            description: PR description/body
            base_branch: Target branch (default: main)
            
        Returns:
            PR info dict with url, number, etc. or None on failure
        """
        if not self.repo_url or not self.token:
            self.logger.error("Git repo URL and token required for PR creation")
            return None
        
        base = base_branch or self.branch
        pr_title = title or f"fix({defect_id}): Apply RCA recommended fix"
        pr_body = description or self._generate_pr_description(defect_id)
        
        # Detect platform from URL
        if 'github.com' in self.repo_url:
            return self._create_github_pr(branch_name, base, pr_title, pr_body)
        elif 'gitlab' in self.repo_url:
            return self._create_gitlab_mr(branch_name, base, pr_title, pr_body)
        elif 'bitbucket' in self.repo_url:
            return self._create_bitbucket_pr(branch_name, base, pr_title, pr_body)
        else:
            self.logger.error(f"Unsupported Git platform: {self.repo_url}")
            return None
    
    def _generate_pr_description(self, defect_id: str) -> str:
        """Generate PR description from defect ID"""
        return f"""## Summary
Automated fix for defect **{defect_id}** based on Root Cause Analysis.

## Changes
- Applied recommended code fix from RCA analysis
- Fix based on pattern matching with historical defects

## Related
- Defect: {defect_id}
- Generated by: RCA Agent

## Testing
- [ ] Unit tests pass
- [ ] Manual testing completed
- [ ] Code review completed

---
*This PR was automatically created by the RCA Agent.*
"""
    
    def _extract_repo_info(self) -> tuple:
        """Extract owner and repo name from URL"""
        # Match patterns like:
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git
        patterns = [
            r'github\.com[:/]([^/]+)/([^/.]+)',
            r'gitlab\.com[:/]([^/]+)/([^/.]+)',
            r'bitbucket\.org[:/]([^/]+)/([^/.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.repo_url)
            if match:
                return match.group(1), match.group(2).replace('.git', '')
        
        return None, None
    
    def _create_github_pr(
        self, 
        head_branch: str, 
        base_branch: str, 
        title: str, 
        body: str
    ) -> Optional[Dict[str, Any]]:
        """Create GitHub Pull Request via API"""
        owner, repo = self._extract_repo_info()
        
        if not owner or not repo:
            self.logger.error("Could not extract owner/repo from URL")
            return None
        
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                pr_data = response.json()
                result = {
                    "platform": "github",
                    "number": pr_data.get("number"),
                    "url": pr_data.get("html_url"),
                    "state": pr_data.get("state"),
                    "title": pr_data.get("title"),
                    "created_at": pr_data.get("created_at")
                }
                self.logger.info(f"Created GitHub PR #{result['number']}: {result['url']}")
                return result
            elif response.status_code == 422:
                # PR might already exist
                error = response.json()
                if "already exists" in str(error):
                    self.logger.warning("PR already exists for this branch")
                    return self._get_existing_github_pr(owner, repo, head_branch)
                else:
                    self.logger.error(f"GitHub API error: {error}")
            else:
                self.logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Failed to create GitHub PR: {e}")
        
        return None
    
    def _get_existing_github_pr(
        self, 
        owner: str, 
        repo: str, 
        head_branch: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing GitHub PR for a branch"""
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        params = {
            "head": f"{owner}:{head_branch}",
            "state": "open"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                prs = response.json()
                if prs:
                    pr = prs[0]
                    return {
                        "platform": "github",
                        "number": pr.get("number"),
                        "url": pr.get("html_url"),
                        "state": pr.get("state"),
                        "title": pr.get("title"),
                        "exists": True
                    }
        except Exception as e:
            self.logger.error(f"Failed to get existing PR: {e}")
        
        return None
    
    def _create_gitlab_mr(
        self, 
        source_branch: str, 
        target_branch: str, 
        title: str, 
        description: str
    ) -> Optional[Dict[str, Any]]:
        """Create GitLab Merge Request via API"""
        owner, repo = self._extract_repo_info()
        
        if not owner or not repo:
            self.logger.error("Could not extract owner/repo from URL")
            return None
        
        # GitLab uses project ID or URL-encoded path
        project_path = f"{owner}%2F{repo}"
        url = f"https://gitlab.com/api/v4/projects/{project_path}/merge_requests"
        headers = {
            "PRIVATE-TOKEN": self.token
        }
        payload = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in (200, 201):
                mr_data = response.json()
                result = {
                    "platform": "gitlab",
                    "number": mr_data.get("iid"),
                    "url": mr_data.get("web_url"),
                    "state": mr_data.get("state"),
                    "title": mr_data.get("title"),
                    "created_at": mr_data.get("created_at")
                }
                self.logger.info(f"Created GitLab MR !{result['number']}: {result['url']}")
                return result
            else:
                self.logger.error(f"GitLab API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Failed to create GitLab MR: {e}")
        
        return None
    
    def _create_bitbucket_pr(
        self, 
        source_branch: str, 
        dest_branch: str, 
        title: str, 
        description: str
    ) -> Optional[Dict[str, Any]]:
        """Create Bitbucket Pull Request via API"""
        owner, repo = self._extract_repo_info()
        
        if not owner or not repo:
            self.logger.error("Could not extract owner/repo from URL")
            return None
        
        url = f"https://api.bitbucket.org/2.0/repositories/{owner}/{repo}/pullrequests"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "title": title,
            "description": description,
            "source": {"branch": {"name": source_branch}},
            "destination": {"branch": {"name": dest_branch}}
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in (200, 201):
                pr_data = response.json()
                result = {
                    "platform": "bitbucket",
                    "number": pr_data.get("id"),
                    "url": pr_data.get("links", {}).get("html", {}).get("href"),
                    "state": pr_data.get("state"),
                    "title": pr_data.get("title"),
                    "created_at": pr_data.get("created_on")
                }
                self.logger.info(f"Created Bitbucket PR #{result['number']}: {result['url']}")
                return result
            else:
                self.logger.error(f"Bitbucket API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Failed to create Bitbucket PR: {e}")
        
        return None
    
    def create_fix_and_pr(
        self,
        defect_id: str,
        file_path: str,
        old_content: str,
        new_content: str,
        commit_message: str = None,
        pr_title: str = None,
        pr_description: str = None
    ) -> Dict[str, Any]:
        """
        Complete workflow: Create branch → Apply fix → Commit → Push → Create PR
        
        Args:
            defect_id: Defect/ticket ID (e.g., "SAM1-2001")
            file_path: Path to file to fix
            old_content: Content to replace
            new_content: New content
            commit_message: Custom commit message
            pr_title: Custom PR title
            pr_description: Custom PR description
            
        Returns:
            Result dict with branch, commit, pr info
        """
        result = {
            "success": False,
            "defect_id": defect_id,
            "branch": None,
            "commit": None,
            "pr": None,
            "errors": []
        }
        
        # Step 1: Create fix branch
        branch_name = self.create_fix_branch(defect_id)
        if not branch_name:
            result["errors"].append("Failed to create branch")
            return result
        result["branch"] = branch_name
        
        # Step 2: Apply fix
        if not self.apply_fix(file_path, old_content, new_content):
            result["errors"].append(f"Failed to apply fix to {file_path}")
            return result
        
        # Step 3: Commit
        commit_hash = self.commit_fix(defect_id, commit_message, [file_path])
        if not commit_hash:
            result["errors"].append("Failed to commit changes")
            return result
        result["commit"] = commit_hash
        
        # Step 4: Push branch
        if not self.push_branch(branch_name):
            result["errors"].append("Failed to push branch")
            return result
        
        # Step 5: Create PR
        pr_info = self.create_pull_request(
            defect_id=defect_id,
            branch_name=branch_name,
            title=pr_title,
            description=pr_description
        )
        
        if pr_info:
            result["pr"] = pr_info
            result["success"] = True
            self.logger.info(f"Successfully created fix PR for {defect_id}: {pr_info.get('url')}")
        else:
            result["errors"].append("Failed to create PR (branch pushed successfully)")
            # PR creation failed but branch is pushed - partial success
            result["partial_success"] = True
        
        return result

    # ==========================================
    # ENTERPRISE GITHUB PR OPERATIONS
    # ==========================================
    
    def create_enterprise_pull_request(
        self,
        defect_id: str,
        branch_name: str,
        title: str = None,
        description: str = None,
        base_branch: str = "master",
        owner: str = None,
        repo: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Pull Request on enterprise GitHub (e.g., cc-github.bmwgroup.net)
        
        Use this for BMW internal repositories instead of public GitHub.
        
        Args:
            defect_id: Defect/ticket ID
            branch_name: Source branch for PR
            title: PR title (auto-generated if not provided)
            description: PR description/body
            base_branch: Target branch (default: master)
            owner: GitHub repository owner (extracted from repo_url if not provided)
            repo: GitHub repository name (extracted from repo_url if not provided)
            
        Returns:
            PR info dict with url, number, etc. or None on failure
        """
        if not self.git_username or not self.token:
            self.logger.error("GitHub credentials not configured. Set GIT_USERNAME and GIT_TOKEN.")
            return None
        
        # Extract owner/repo from URL if not provided
        if not owner or not repo:
            owner, repo = self._extract_repo_info()
            if not owner or not repo:
                self.logger.error("Could not extract owner/repo from URL")
                return None
        
        pr_title = title or f"fix({defect_id}): Apply RCA recommended fix"
        pr_body = description or self._generate_pr_description(defect_id)
        
        url = f"{self.github_enterprise_url}/repos/{owner}/{repo}/pulls"
        headers = {"Content-Type": "application/json"}
        payload = {
            "title": pr_title,
            "head": f"{self.git_username}:{branch_name}",
            "base": base_branch,
            "body": pr_body
        }
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                auth=(self.git_username, self.token), 
                json=payload, 
                verify=False  # May be needed for enterprise certs
            )
            
            if response.status_code in (200, 201):
                pr_data = response.json()
                result = {
                    "platform": "github_enterprise",
                    "number": pr_data.get("number"),
                    "url": pr_data.get("html_url"),
                    "state": pr_data.get("state"),
                    "title": pr_data.get("title"),
                    "created_at": pr_data.get("created_at")
                }
                self.logger.info(f"Created Enterprise GitHub PR #{result['number']}: {result['url']}")
                return result
            elif response.status_code == 422:
                # PR might already exist
                error = response.json()
                if "already exists" in str(error):
                    self.logger.warning("PR already exists for this branch")
                    return self._get_existing_enterprise_pr(owner, repo, branch_name)
                else:
                    self.logger.error(f"Enterprise GitHub API error: {error}")
            else:
                self.logger.error(f"Enterprise GitHub API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Failed to create Enterprise GitHub PR: {e}")
        
        return None
    
    def _get_existing_enterprise_pr(
        self, 
        owner: str, 
        repo: str, 
        head_branch: str
    ) -> Optional[Dict[str, Any]]:
        """Get existing Enterprise GitHub PR for a branch"""
        url = f"{self.github_enterprise_url}/repos/{owner}/{repo}/pulls"
        headers = {"Accept": "application/vnd.github.v3+json"}
        params = {
            "head": f"{owner}:{head_branch}",
            "state": "open"
        }
        
        try:
            response = requests.get(
                url, 
                headers=headers, 
                params=params,
                auth=(self.git_username, self.token),
                verify=False
            )
            if response.status_code == 200:
                prs = response.json()
                if prs:
                    pr = prs[0]
                    return {
                        "platform": "github_enterprise",
                        "number": pr.get("number"),
                        "url": pr.get("html_url"),
                        "state": pr.get("state"),
                        "title": pr.get("title"),
                        "exists": True
                    }
        except Exception as e:
            self.logger.error(f"Failed to get existing PR: {e}")
        
        return None
    
    def check_enterprise_pr_status(
        self, 
        pr_number: int, 
        owner: str = None, 
        repo: str = None
    ) -> Dict[str, Any]:
        """
        Check the status of a Pull Request on enterprise GitHub
        
        Args:
            pr_number: PR number to check
            owner: Repo owner (extracted from repo_url if not provided)
            repo: Repo name (extracted from repo_url if not provided)
            
        Returns:
            PR status information
        """
        if not owner or not repo:
            owner, repo = self._extract_repo_info()
        
        url = f"{self.github_enterprise_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {"Accept": "application/json"}
        
        try:
            response = requests.get(
                url,
                headers=headers,
                auth=(self.git_username, self.token),
                verify=False
            )
            
            if response.status_code == 200:
                pr_data = response.json()
                return {
                    "success": True,
                    "number": pr_data.get("number"),
                    "state": pr_data.get("state"),
                    "merged": pr_data.get("merged", False),
                    "title": pr_data.get("title"),
                    "url": pr_data.get("html_url"),
                    "created_at": pr_data.get("created_at"),
                    "updated_at": pr_data.get("updated_at")
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to get PR status: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    def create_fix_and_enterprise_pr(
        self,
        defect_id: str,
        file_path: str,
        old_content: str,
        new_content: str,
        commit_message: str = None,
        pr_title: str = None,
        pr_description: str = None
    ) -> Dict[str, Any]:
        """
        Complete workflow for enterprise GitHub: Create branch → Apply fix → Commit → Push → Create PR
        
        Use this for BMW internal repositories (cc-github.bmwgroup.net).
        
        Args:
            defect_id: Defect/ticket ID (e.g., "SAM1-2001")
            file_path: Path to file to fix
            old_content: Content to replace
            new_content: New content
            commit_message: Custom commit message
            pr_title: Custom PR title
            pr_description: Custom PR description
            
        Returns:
            Result dict with branch, commit, pr info
        """
        result = {
            "success": False,
            "defect_id": defect_id,
            "branch": None,
            "commit": None,
            "pr": None,
            "errors": []
        }
        
        # Step 1: Create fix branch
        branch_name = self.create_fix_branch(defect_id)
        if not branch_name:
            result["errors"].append("Failed to create branch")
            return result
        result["branch"] = branch_name
        
        # Step 2: Apply fix
        if not self.apply_fix(file_path, old_content, new_content):
            result["errors"].append(f"Failed to apply fix to {file_path}")
            return result
        
        # Step 3: Commit
        commit_hash = self.commit_fix(defect_id, commit_message, [file_path])
        if not commit_hash:
            result["errors"].append("Failed to commit changes")
            return result
        result["commit"] = commit_hash
        
        # Step 4: Push branch
        if not self.push_branch(branch_name):
            result["errors"].append("Failed to push branch")
            return result
        
        # Step 5: Create PR on enterprise GitHub
        pr_info = self.create_enterprise_pull_request(
            defect_id=defect_id,
            branch_name=branch_name,
            title=pr_title,
            description=pr_description
        )
        
        if pr_info:
            result["pr"] = pr_info
            result["success"] = True
            self.logger.info(f"Successfully created enterprise fix PR for {defect_id}: {pr_info.get('url')}")
        else:
            result["errors"].append("Failed to create PR (branch pushed successfully)")
            result["partial_success"] = True
        
        return result