"""
RCA Engine - Core orchestration for Root Cause Analysis

This module coordinates:
1. Defect loading from JIRA
2. DLT log parsing
3. Source code mapping (local or Git repository)
4. Historical defect matching
5. Domain knowledge lookup (MD files)
6. LLM analysis
7. Report generation
8. JIRA updates (comments, attachments, duplicate marking)
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import glob

from .dlt_analyzer import DLTAnalyzer
from .source_mapper import SourceMapper
from .historical_matcher import HistoricalMatcher
from .report_generator import ReportGenerator
from .html_report_generator import generate_rca_html_report, save_html_report

# Optional dashboard integration for live monitoring
try:
    from .dashboard.dashboard_server import RCADashboard
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    RCADashboard = None

# Optional ML-based domain classifier
try:
    from .domain_classifier import DomainClassifier, predict_domain_for_defect
    DOMAIN_CLASSIFIER_AVAILABLE = True
except ImportError:
    DOMAIN_CLASSIFIER_AVAILABLE = False
    DomainClassifier = None


class RCAEngine:
    """
    Main RCA Engine for Infotainment Systems
    
    Orchestrates the complete RCA workflow:
    - Load defect from JIRA or local file
    - Parse associated DLT logs
    - Map to source code (supports Git repository)
    - Find similar historical defects
    - Run LLM analysis
    - Generate reports (MD + HTML)
    - Update JIRA (comment, attachments, duplicate marking)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize RCA Engine
        
        Args:
            config: Configuration dictionary with all settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.dlt_analyzer = DLTAnalyzer(config)
        self.source_mapper = SourceMapper(config)
        self.historical_matcher = HistoricalMatcher(config)
        self.report_generator = ReportGenerator(config)
        
        # External service clients - will be injected
        self.llm_client = None
        self.jira_client = None
        self.git_client = None  # Git repository for source code
        
        # Dashboard for live monitoring (optional)
        self.dashboard = None
        self._token_metrics = {}  # Track tokens per analysis
        
        # Paths
        self.base_path = config.get('paths', {}).get('base_path', '.')
        self.output_dir = config.get('paths', {}).get('output_dir', 'output/reports')
        self.dlt_logs_dir = config.get('paths', {}).get('dlt_logs_dir', 'data/dlt_logs')
        self.defects_dir = config.get('paths', {}).get('defects_dir', 'data/defects')
        self.knowledge_dir = config.get('paths', {}).get('knowledge_dir', 'data/knowledge_base/domain_knowledge')
        
        # Load domain knowledge from MD files
        self.domain_knowledge = self._load_domain_knowledge()
        
        # ML-based domain classifier (optional)
        self.domain_classifier = None
        if DOMAIN_CLASSIFIER_AVAILABLE:
            try:
                self.domain_classifier = DomainClassifier()
                if self.domain_classifier.is_available():
                    self.logger.info("Domain classifier loaded successfully")
                else:
                    self.logger.warning("Domain classifier model not found - using fallback")
            except Exception as e:
                self.logger.warning(f"Failed to initialize domain classifier: {e}")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.logger.info("RCA Engine initialized")
    
    def set_llm_client(self, llm_client):
        """
        Set the LLM client for analysis
        
        Args:
            llm_client: LLM client instance (Azure OpenAI, OpenAI, etc.)
        """
        self.llm_client = llm_client
        self.logger.info("LLM client configured")
    
    def set_jira_client(self, jira_client):
        """
        Set the JIRA client for integration
        
        Args:
            jira_client: JIRA client instance
        """
        self.jira_client = jira_client
        self.logger.info("JIRA client configured")
    
    def set_git_client(self, git_client):
        """
        Set the Git client for source code access
        
        PLACEHOLDER: Configure with your Git repository
        The Git client provides access to source code for:
        - Mapping DLT errors to source files
        - Getting code context for LLM analysis
        - Finding related files by component
        
        Args:
            git_client: Git client instance (GitService)
        """
        self.git_client = git_client
        self.logger.info("Git client configured")
    
    def set_dashboard(self, dashboard):
        """
        Set the dashboard for real-time monitoring
        
        Args:
            dashboard: RCADashboard instance for live tracking
        """
        self.dashboard = dashboard
        self.logger.info("Dashboard configured for live monitoring")
    
    def _track_tokens(
        self,
        defect_id: str,
        stage: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "claude-sonnet"
    ):
        """
        Track token consumption for a stage
        
        Updates both internal metrics and dashboard (if available)
        
        Args:
            defect_id: Defect ID being analyzed
            stage: Current analysis stage
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name for cost calculation
        """
        total = input_tokens + output_tokens
        
        # Model multipliers for cost calculation
        MODEL_MULTIPLIERS = {
            'gpt-4o': 0.0, 'gpt-5-mini': 0.0,
            'claude-haiku': 0.33, 'gemini-flash': 0.33,
            'claude-sonnet': 1.0, 'gpt-5': 1.0,
            'claude-opus': 3.0
        }
        
        multiplier = MODEL_MULTIPLIERS.get(model.lower(), 1.0)
        quota_cost = total * multiplier / 1000
        cost_eur = quota_cost * 37.0 / 1000  # €37 per 1000 quota units
        
        # Update internal metrics
        if defect_id in self._token_metrics:
            metrics = self._token_metrics[defect_id]
            
            # Initialize stage if not exists
            if "by_stage" not in metrics:
                metrics["by_stage"] = {}
            if stage not in metrics["by_stage"]:
                metrics["by_stage"][stage] = {"input": 0, "output": 0, "total": 0}
            
            # Increment tokens
            metrics["by_stage"][stage]["input"] += input_tokens
            metrics["by_stage"][stage]["output"] += output_tokens
            metrics["by_stage"][stage]["total"] += total
            
            metrics["total_input"] = metrics.get("total_input", 0) + input_tokens
            metrics["total_output"] = metrics.get("total_output", 0) + output_tokens
            metrics["total_tokens"] = metrics.get("total_tokens", 0) + total
            metrics["estimated_cost_eur"] = metrics.get("estimated_cost_eur", 0) + cost_eur
        
        # Send to dashboard for live update
        if self.dashboard:
            self.dashboard.add_tokens(defect_id, stage, input_tokens, output_tokens)
        
        self.logger.debug(f"Tracked tokens for {defect_id}/{stage}: +{total} tokens")
    
    def _run_llm_analysis_with_tracking(
        self,
        defect_id: str,
        defect_data: Dict[str, Any],
        dlt_analysis: Dict[str, Any],
        source_mapping: Dict[str, Any],
        historical_matches: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run LLM-powered root cause analysis with token tracking
        
        Same as _run_llm_analysis but tracks token consumption incrementally
        """
        # Build analysis prompt
        prompt = self._build_analysis_prompt(
            defect_data, dlt_analysis, source_mapping, historical_matches
        )
        
        # Estimate input tokens (rough: 4 chars per token)
        estimated_input_tokens = len(prompt) // 4
        
        # If LLM client is configured, use it
        if self.llm_client:
            try:
                # Track prompt tokens before calling LLM
                self._track_tokens(defect_id, "llm_analysis", estimated_input_tokens, 0)
                
                response = self.llm_client.analyze_text(
                    prompt=prompt,
                    system_message=self._get_system_prompt()
                )
                
                # Estimate output tokens from response
                response_text = response if isinstance(response, str) else str(response.get("content", response))
                estimated_output_tokens = len(response_text) // 4
                
                # Track response tokens
                self._track_tokens(defect_id, "llm_analysis", 0, estimated_output_tokens)
                
                return self._parse_llm_response(response)
            except Exception as e:
                self.logger.error(f"LLM analysis failed: {e}")
                return self._generate_mock_analysis(defect_data, dlt_analysis)
        else:
            # Return mock analysis when LLM not configured
            self.logger.warning("LLM client not configured, using mock analysis")
            
            # Track simulated tokens for mock analysis
            self._track_tokens(defect_id, "llm_analysis", estimated_input_tokens, 500)
            
            return self._generate_mock_analysis(defect_data, dlt_analysis)

    # ==========================================
    # DOMAIN KNOWLEDGE METHODS
    # ==========================================
    
    def _load_domain_knowledge(self) -> Dict[str, Any]:
        """
        Load domain knowledge from MD files in knowledge_base directory
        
        Returns:
            Dictionary with loaded knowledge organized by topic
        """
        knowledge = {
            "files": {},           # filename -> content
            "app_id_mapping": {},  # APP_ID -> component name
            "ctx_id_mapping": {},  # CTX_ID -> sub-component
            "patterns": [],        # Pattern -> root cause lookup
            "kpi_thresholds": {},  # KPI definitions
        }
        
        if not os.path.exists(self.knowledge_dir):
            self.logger.warning(f"Knowledge directory not found: {self.knowledge_dir}")
            return knowledge
        
        # Load all MD files
        md_files = glob.glob(os.path.join(self.knowledge_dir, "*.md"))
        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    filename = os.path.basename(md_file)
                    knowledge["files"][filename] = content
                    
                    # Extract specific knowledge based on file type
                    if "dlt_logging" in filename.lower():
                        self._extract_app_ctx_mappings(content, knowledge)
                    elif "rca_quick" in filename.lower():
                        self._extract_patterns(content, knowledge)
                    elif "kpi" in filename.lower():
                        self._extract_kpi_thresholds(content, knowledge)
                    
                    self.logger.debug(f"Loaded knowledge: {filename}")
                    
            except Exception as e:
                self.logger.error(f"Failed to load {md_file}: {e}")
        
        self.logger.info(f"Loaded {len(knowledge['files'])} domain knowledge files")
        return knowledge
    
    def _extract_app_ctx_mappings(self, content: str, knowledge: Dict):
        """Extract APP_ID and CTX_ID mappings from DLT guide"""
        # Pattern for APP_ID table rows: | `MDIA` | MediaService | description |
        app_pattern = r'\|\s*`?(\w{4})`?\s*\|\s*([^|]+)\s*\|'
        
        # Look for APP_ID section
        app_section = re.search(r'Application IDs.*?(?=##|$)', content, re.DOTALL | re.IGNORECASE)
        if app_section:
            for match in re.finditer(app_pattern, app_section.group()):
                app_id = match.group(1).upper()
                component = match.group(2).strip()
                if app_id and len(app_id) == 4 and component:
                    knowledge["app_id_mapping"][app_id] = component
        
        # Look for CTX_ID sections
        ctx_section = re.search(r'Context IDs.*?(?=##[^#]|$)', content, re.DOTALL | re.IGNORECASE)
        if ctx_section:
            for match in re.finditer(app_pattern, ctx_section.group()):
                ctx_id = match.group(1).upper()
                desc = match.group(2).strip()
                if ctx_id and len(ctx_id) == 4 and desc:
                    knowledge["ctx_id_mapping"][ctx_id] = desc
    
    def _extract_patterns(self, content: str, knowledge: Dict):
        """Extract pattern -> root cause mappings from RCA quick reference"""
        # Pattern for table rows: | pattern | root cause | component | fix |
        pattern_regex = r'\|\s*`?([^|]+)`?\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
        
        for match in re.finditer(pattern_regex, content):
            pattern = match.group(1).strip().strip('`')  # Remove backticks
            root_cause = match.group(2).strip()
            component = match.group(3).strip()
            fix = match.group(4).strip()
            
            # Skip header rows
            if 'Pattern' in pattern or 'Root Cause' in root_cause or '---' in pattern:
                continue
            
            if pattern and root_cause:
                knowledge["patterns"].append({
                    "pattern": pattern,
                    "root_cause": root_cause,
                    "component": component,
                    "fix": fix
                })
    
    def _extract_kpi_thresholds(self, content: str, knowledge: Dict):
        """Extract KPI threshold definitions"""
        # Look for threshold patterns like: STR < 200ms, Boot < 3000ms
        threshold_patterns = [
            (r'STR.*?(\d+)\s*ms', 'STR'),
            (r'LUM.*?(\d+)\s*ms', 'LUM'),
            (r'Boot.*?(\d+)\s*ms', 'BOOT'),
            (r'Cold Boot.*?(\d+)\s*ms', 'COLD_BOOT'),
        ]
        
        for pattern, kpi_name in threshold_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                knowledge["kpi_thresholds"][kpi_name] = int(match.group(1))
    
    def _get_relevant_knowledge(
        self, 
        dlt_analysis: Dict[str, Any],
        defect_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get relevant domain knowledge based on DLT analysis and defect data
        
        Args:
            dlt_analysis: Parsed DLT log analysis
            defect_data: Defect information
            
        Returns:
            Dictionary with relevant knowledge sections
        """
        relevant = {
            "matched_patterns": [],
            "component_info": [],
            "kpi_context": [],
            "relevant_files": []
        }
        
        # Get detected APP_IDs and components from DLT
        app_ids = dlt_analysis.get("app_ids", [])
        components = dlt_analysis.get("components", [])
        patterns_detected = dlt_analysis.get("patterns", [])
        
        # Match patterns from RCA quick reference
        for error in dlt_analysis.get("errors", []) + dlt_analysis.get("warnings", []):
            message = error.get("message", "")
            for pattern_info in self.domain_knowledge.get("patterns", []):
                pattern = pattern_info.get("pattern", "")
                try:
                    if re.search(pattern, message, re.IGNORECASE):
                        relevant["matched_patterns"].append({
                            "detected_message": message[:100],
                            "matched_pattern": pattern,
                            "likely_root_cause": pattern_info.get("root_cause"),
                            "affected_component": pattern_info.get("component"),
                            "recommended_fix": pattern_info.get("fix")
                        })
                except re.error:
                    # Pattern might be literal string, try exact match
                    if pattern.lower() in message.lower():
                        relevant["matched_patterns"].append({
                            "detected_message": message[:100],
                            "matched_pattern": pattern,
                            "likely_root_cause": pattern_info.get("root_cause"),
                            "affected_component": pattern_info.get("component"),
                            "recommended_fix": pattern_info.get("fix")
                        })
        
        # Get component info from APP_ID mappings
        for app_id in app_ids:
            if app_id in self.domain_knowledge.get("app_id_mapping", {}):
                relevant["component_info"].append({
                    "app_id": app_id,
                    "component": self.domain_knowledge["app_id_mapping"][app_id]
                })
        
        # Check KPI thresholds if relevant
        defect_summary = defect_data.get("summary", "").lower()
        defect_desc = defect_data.get("description", "").lower()
        
        kpi_keywords = {
            "STR": ["str", "source transition", "source switch"],
            "LUM": ["lum", "last user mode", "preset"],
            "BOOT": ["boot", "startup", "cold start"]
        }
        
        for kpi, keywords in kpi_keywords.items():
            if any(kw in defect_summary or kw in defect_desc for kw in keywords):
                threshold = self.domain_knowledge.get("kpi_thresholds", {}).get(kpi)
                if threshold:
                    relevant["kpi_context"].append({
                        "kpi": kpi,
                        "threshold_ms": threshold,
                        "note": f"{kpi} must complete in < {threshold}ms"
                    })
        
        # Find relevant knowledge files based on components
        component_to_file = {
            "audio": "01_audio_subsystem.md",
            "bluetooth": "02_bluetooth_connectivity.md",
            "bt": "02_bluetooth_connectivity.md",
            "dlt": "03_dlt_logging_guide.md",
            "boot": "04_boot_and_system.md",
            "can": "05_vehicle_bus_communication.md",
            "most": "05_vehicle_bus_communication.md",
            "kpi": "06_kpi_definitions.md",
        }
        
        for component in components:
            comp_lower = component.lower()
            for keyword, filename in component_to_file.items():
                if keyword in comp_lower:
                    if filename in self.domain_knowledge.get("files", {}):
                        relevant["relevant_files"].append(filename)
        
        # Also check defect summary/description
        for keyword, filename in component_to_file.items():
            if keyword in defect_summary or keyword in defect_desc:
                if filename in self.domain_knowledge.get("files", {}):
                    if filename not in relevant["relevant_files"]:
                        relevant["relevant_files"].append(filename)
        
        return relevant

    def analyze_defect(
        self,
        defect_id: str,
        from_jira: bool = False,
        upload_to_jira: bool = True,
        mark_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        Perform complete RCA for a defect
        
        Args:
            defect_id: Defect ID (e.g., SAM1-2001)
            from_jira: If True, fetch defect from JIRA API
            upload_to_jira: If True, upload reports and comment to JIRA
            mark_duplicates: If True, mark duplicate ticket if found
            
        Returns:
            Complete RCA result dictionary
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"Starting RCA for defect: {defect_id}")
        
        # Initialize token tracking for this analysis
        self._token_metrics[defect_id] = {
            "by_stage": {},
            "total_input": 0,
            "total_output": 0,
            "total_tokens": 0,
            "estimated_cost_eur": 0.0
        }
        
        # Notify dashboard if available
        if self.dashboard:
            defect_preview = {"summary": "", "component": "Unknown", "priority": "Medium"}
            self.dashboard.start_analysis(defect_id, defect_preview)
        
        result = {
            "defect_id": defect_id,
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
            "stages": {}
        }
        
        try:
            # Stage 1: Load defect data
            self.logger.info("Stage 1: Loading defect data")
            if self.dashboard:
                self.dashboard.update_stage(defect_id, "defect_loading", "running")
            
            defect_data = self._load_defect(defect_id, from_jira)
            result["stages"]["load_defect"] = {"status": "success", "data": defect_data}
            
            # Domain Classification (ML-based)
            domain_prediction = None
            if self.domain_classifier:
                self.logger.info("Running ML-based domain classification")
                domain_prediction = self.domain_classifier.predict_from_defect(defect_data)
                defect_data["predicted_domain"] = domain_prediction["domain"]
                defect_data["predicted_domain_display"] = domain_prediction["domain_display"]
                defect_data["predicted_domain_confidence"] = domain_prediction["confidence"]
                defect_data["assigned_team"] = domain_prediction["team"]
                result["stages"]["domain_classification"] = {
                    "status": "success",
                    "data": domain_prediction
                }
                self.logger.info(f"Domain prediction: {domain_prediction['domain_display']} "
                               f"(confidence: {domain_prediction['confidence']:.0%})")
            
            # Update dashboard with defect info
            if self.dashboard:
                self.dashboard.update_stage(defect_id, "defect_loading", "completed")
                # Update with actual defect info including predicted domain
                predicted_domain = domain_prediction["domain_short"] if domain_prediction else "Unknown"
                self.dashboard.start_analysis(defect_id, {
                    "summary": defect_data.get("summary", "")[:100],
                    "component": defect_data.get("component", "Unknown"),
                    "priority": defect_data.get("priority", "Medium"),
                    "predicted_domain": predicted_domain
                })
            
            # Stage 2: Parse DLT logs
            self.logger.info("Stage 2: Parsing DLT logs")
            if self.dashboard:
                self.dashboard.update_stage(defect_id, "dlt_analysis", "running")
            
            dlt_analysis = self._analyze_dlt_logs(defect_data)
            result["stages"]["dlt_analysis"] = {"status": "success", "data": dlt_analysis}
            
            if self.dashboard:
                self.dashboard.update_stage(defect_id, "dlt_analysis", "completed")
            
            # Stage 3: Map to source code
            self.logger.info("Stage 3: Mapping to source code")
            if self.dashboard:
                self.dashboard.update_stage(defect_id, "source_mapping", "running")
            
            source_mapping = self._map_source_code(dlt_analysis)
            result["stages"]["source_mapping"] = {"status": "success", "data": source_mapping}
            
            if self.dashboard:
                self.dashboard.update_stage(defect_id, "source_mapping", "completed")
            
            # Stage 4: Search historical defects
            self.logger.info("Stage 4: Searching historical defects")
            if self.dashboard:
                self.dashboard.update_stage(defect_id, "historical_match", "running")
            
            historical_matches = self._search_historical(defect_data, dlt_analysis)
            result["stages"]["historical_search"] = {"status": "success", "data": historical_matches}
            
            if self.dashboard:
                self.dashboard.update_stage(defect_id, "historical_match", "completed")
            
            # Check for duplicates
            duplicate_info = self._check_duplicates(historical_matches)
            result["duplicate_info"] = duplicate_info
            
            # Stage 5: LLM Analysis (main token consumer)
            self.logger.info("Stage 5: Running LLM analysis")
            if self.dashboard:
                self.dashboard.update_stage(defect_id, "llm_analysis", "running")
            
            llm_analysis = self._run_llm_analysis_with_tracking(
                defect_id, defect_data, dlt_analysis, source_mapping, historical_matches
            )
            result["stages"]["llm_analysis"] = {"status": "success", "data": llm_analysis}
            
            if self.dashboard:
                self.dashboard.update_stage(defect_id, "llm_analysis", "completed")
                # Update confidence
                confidence = llm_analysis.get("confidence", 0)
                domain = llm_analysis.get("domain", defect_data.get("component", "Unknown"))
                self.dashboard.update_confidence(defect_id, confidence, domain)
            
            # Stage 6: Generate Reports (MD + HTML)
            self.logger.info("Stage 6: Generating reports")
            if self.dashboard:
                self.dashboard.update_stage(defect_id, "report_generation", "running")
            
            # Add token metrics to llm_analysis for report
            llm_analysis["token_metrics"] = self._token_metrics.get(defect_id, {})
            
            reports = self._generate_reports(
                defect_id, defect_data, dlt_analysis, source_mapping, 
                historical_matches, llm_analysis, duplicate_info
            )
            result["stages"]["report_generation"] = {"status": "success", "data": reports}
            result["reports"] = reports
            
            if self.dashboard:
                self.dashboard.update_stage(defect_id, "report_generation", "completed")
            
            # Stage 7: JIRA Integration (if enabled)
            if upload_to_jira and self.jira_client:
                self.logger.info("Stage 7: Updating JIRA")
                jira_result = self._update_jira(
                    defect_id, llm_analysis, reports, duplicate_info, mark_duplicates,
                    defect_data, dlt_analysis
                )
                result["stages"]["jira_update"] = {"status": "success", "data": jira_result}
            
            result["status"] = "completed"
            result["root_cause"] = llm_analysis.get("root_cause", "Unknown")
            result["confidence"] = llm_analysis.get("confidence", 0.0)
            result["token_metrics"] = self._token_metrics.get(defect_id, {})
            result["duration_seconds"] = time.time() - start_time
            
            # Complete dashboard tracking
            if self.dashboard:
                self.dashboard.complete_analysis(defect_id, success=True)
            
            self.logger.info(f"RCA completed for {defect_id}")
            
        except Exception as e:
            self.logger.error(f"RCA failed: {str(e)}")
            result["status"] = "failed"
            result["error"] = str(e)
            
            # Complete dashboard tracking on failure
            if self.dashboard:
                self.dashboard.complete_analysis(defect_id, success=False)
        
        return result
    
    def _load_defect(self, defect_id: str, from_jira: bool) -> Dict[str, Any]:
        """Load defect data from JIRA or local file"""
        if from_jira and self.jira_client:
            # Placeholder: Fetch from JIRA API
            return self.jira_client.get_issue(defect_id)
        else:
            # Try multiple local JSON files
            files_to_check = [
                os.path.join(self.defects_dir, "test_defect.json"),
                os.path.join(self.defects_dir, "jira_api_defects.json"),
                os.path.join(self.defects_dir, "historical_defects.json"),
            ]
            
            for defects_file in files_to_check:
                if os.path.exists(defects_file):
                    with open(defects_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Handle both formats: list or {"defects": [...]}
                        if isinstance(data, list):
                            defects_list = data
                        elif isinstance(data, dict):
                            defects_list = data.get("defects", [data])
                        else:
                            continue
                        
                        for defect in defects_list:
                            if defect.get("key") == defect_id:
                                return defect
            
            raise ValueError(f"Defect {defect_id} not found in local files")
    
    def _analyze_dlt_logs(self, defect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse DLT logs associated with defect (supports binary and text formats)"""
        dlt_content = defect_data.get("dlt_content", "")
        dlt_file = defect_data.get("dlt_attachment", "")
        
        # Try to find DLT file from multiple sources
        dlt_path = None
        
        # Source 1: Direct dlt_attachment field
        if dlt_file:
            possible_path = os.path.join(self.dlt_logs_dir, dlt_file)
            if os.path.exists(possible_path):
                dlt_path = possible_path
        
        # Source 2: Check attachments array (from JIRA)
        if not dlt_path:
            attachments = defect_data.get("attachments", [])
            for att in attachments:
                filename = att.get("filename", "")
                if filename.lower().endswith(('.dlt', '.log', '.txt')):
                    possible_path = os.path.join(self.dlt_logs_dir, filename)
                    if os.path.exists(possible_path):
                        dlt_path = possible_path
                        self.logger.info(f"Found DLT file from attachments: {filename}")
                        break
        
        # Source 3: Scan dlt_logs_dir for any DLT files
        if not dlt_path and os.path.isdir(self.dlt_logs_dir):
            for f in os.listdir(self.dlt_logs_dir):
                if f.lower().endswith(('.dlt', '.log', '.txt')):
                    dlt_path = os.path.join(self.dlt_logs_dir, f)
                    self.logger.info(f"Found DLT file in workspace: {f}")
                    break
        
        # Analyze the DLT file
        if dlt_path and os.path.exists(dlt_path):
            self.logger.info(f"Analyzing DLT file: {dlt_path}")
            return self.dlt_analyzer.analyze_file(dlt_path)
        
        # If content is provided as string, use text parser
        if dlt_content:
            return self.dlt_analyzer.analyze(dlt_content)
        
        # No DLT data found - return empty analysis
        self.logger.warning("No DLT content or file found for analysis")
        return {
            "total_entries": 0,
            "errors": [],
            "warnings": [],
            "components": [],
            "patterns": []
        }
    
    def _map_source_code(self, dlt_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map DLT patterns to source code files
        
        Uses Git repository if configured, otherwise uses local file mapping.
        """
        # Get basic mapping from source mapper
        mapping = self.source_mapper.map_to_source(dlt_analysis)
        
        # Enhance with Git repository if available
        if self.git_client and self.git_client.is_connected():
            try:
                # Pull latest code if auto_pull enabled
                git_config = self.config.get('integrations', {}).get('git', {})
                if git_config.get('auto_pull', True):
                    self.git_client.pull_latest()
                
                # Get actual source code for mapped files
                source_code = self.git_client.get_source_for_mapping(mapping.get('mapped_files', []))
                mapping['source_code'] = source_code
                mapping['git_enabled'] = True
                
                # Add code context for errors
                if dlt_analysis.get('errors'):
                    code_contexts = []
                    for error in dlt_analysis['errors'][:5]:
                        component = error.get('component', '')
                        related_files = self.git_client.find_related_files(component)
                        if related_files:
                            code_contexts.append({
                                'component': component,
                                'files': related_files[:3]
                            })
                    mapping['code_contexts'] = code_contexts
                
            except Exception as e:
                self.logger.warning(f"Git source mapping failed: {e}")
                mapping['git_enabled'] = False
        else:
            mapping['git_enabled'] = False
            mapping['source_code'] = {}
        
        return mapping
    
    def _search_historical(
        self, 
        defect_data: Dict[str, Any], 
        dlt_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Search for similar historical defects"""
        return self.historical_matcher.search(defect_data, dlt_analysis)
    
    def _check_duplicates(self, historical_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check if defect is a duplicate"""
        duplicate_threshold = self.config.get('thresholds', {}).get('duplicate', 0.90)
        
        duplicate_info = {
            "is_duplicate": False,
            "duplicate_of": None,
            "similarity_score": 0.0,
            "related_defects": []
        }
        
        if historical_matches:
            top_match = historical_matches[0]
            similarity = top_match.get("similarity_score", 0)
            
            if similarity >= duplicate_threshold:
                duplicate_info["is_duplicate"] = True
                duplicate_info["duplicate_of"] = top_match.get("defect_id")
                duplicate_info["similarity_score"] = similarity
            
            # Collect related defects (above related threshold)
            related_threshold = self.config.get('thresholds', {}).get('related', 0.75)
            duplicate_info["related_defects"] = [
                m for m in historical_matches 
                if m.get("similarity_score", 0) >= related_threshold
            ]
        
        return duplicate_info
    
    def _run_llm_analysis(
        self,
        defect_data: Dict[str, Any],
        dlt_analysis: Dict[str, Any],
        source_mapping: Dict[str, Any],
        historical_matches: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run LLM-powered root cause analysis"""
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(
            defect_data, dlt_analysis, source_mapping, historical_matches
        )
        
        # If LLM client is configured, use it
        if self.llm_client:
            try:
                response = self.llm_client.analyze_text(
                    prompt=prompt,
                    system_message=self._get_system_prompt()
                )
                return self._parse_llm_response(response)
            except Exception as e:
                self.logger.error(f"LLM analysis failed: {e}")
                return self._generate_mock_analysis(defect_data, dlt_analysis)
        else:
            # Return mock analysis when LLM not configured
            self.logger.warning("LLM client not configured, using mock analysis")
            return self._generate_mock_analysis(defect_data, dlt_analysis)
    
    def _build_analysis_prompt(
        self,
        defect_data: Dict[str, Any],
        dlt_analysis: Dict[str, Any],
        source_mapping: Dict[str, Any],
        historical_matches: List[Dict[str, Any]]
    ) -> str:
        """Build comprehensive prompt for LLM analysis including domain knowledge"""
        
        prompt_parts = []
        
        # Defect information
        prompt_parts.append("## DEFECT INFORMATION")
        prompt_parts.append(f"ID: {defect_data.get('key', 'Unknown')}")
        prompt_parts.append(f"Summary: {defect_data.get('summary', 'No summary')}")
        prompt_parts.append(f"Description: {defect_data.get('description', 'No description')}")
        prompt_parts.append(f"Component: {defect_data.get('component', 'Unknown')}")
        prompt_parts.append(f"Priority: {defect_data.get('priority', 'Unknown')}")
        prompt_parts.append("")
        
        # DLT Analysis
        prompt_parts.append("## DLT LOG ANALYSIS")
        if dlt_analysis.get("errors"):
            prompt_parts.append("### Errors Found:")
            for error in dlt_analysis["errors"][:10]:
                prompt_parts.append(f"- {error}")
        if dlt_analysis.get("warnings"):
            prompt_parts.append("### Warnings Found:")
            for warning in dlt_analysis["warnings"][:5]:
                prompt_parts.append(f"- {warning}")
        if dlt_analysis.get("components"):
            prompt_parts.append(f"### Affected Components: {', '.join(dlt_analysis['components'])}")
        prompt_parts.append("")
        
        # DOMAIN KNOWLEDGE CONTEXT (NEW)
        relevant_knowledge = self._get_relevant_knowledge(dlt_analysis, defect_data)
        
        if relevant_knowledge.get("matched_patterns") or relevant_knowledge.get("component_info") or relevant_knowledge.get("kpi_context"):
            prompt_parts.append("## DOMAIN KNOWLEDGE CONTEXT")
            prompt_parts.append("(From automotive infotainment domain expertise)")
            prompt_parts.append("")
            
            # Pattern matches from RCA quick reference
            if relevant_knowledge.get("matched_patterns"):
                prompt_parts.append("### PATTERN → ROOT CAUSE MATCHES (from knowledge base):")
                for match in relevant_knowledge["matched_patterns"][:5]:
                    prompt_parts.append(f"- **Pattern Detected:** `{match.get('matched_pattern')}`")
                    prompt_parts.append(f"  - **Likely Root Cause:** {match.get('likely_root_cause')}")
                    prompt_parts.append(f"  - **Affected Component:** {match.get('affected_component')}")
                    prompt_parts.append(f"  - **Recommended Fix Area:** {match.get('recommended_fix')}")
                prompt_parts.append("")
            
            # Component identification from APP_ID
            if relevant_knowledge.get("component_info"):
                prompt_parts.append("### COMPONENT IDENTIFICATION (from DLT APP_ID):")
                for info in relevant_knowledge["component_info"]:
                    prompt_parts.append(f"- APP_ID `{info.get('app_id')}` → {info.get('component')}")
                prompt_parts.append("")
            
            # KPI thresholds
            if relevant_knowledge.get("kpi_context"):
                prompt_parts.append("### KPI THRESHOLDS (from domain knowledge):")
                for kpi in relevant_knowledge["kpi_context"]:
                    prompt_parts.append(f"- **{kpi.get('kpi')}**: {kpi.get('note')}")
                prompt_parts.append("")
            
            prompt_parts.append("")
        
        # Source Mapping
        prompt_parts.append("## SOURCE CODE MAPPING")
        if source_mapping.get("mapped_files"):
            for file_info in source_mapping["mapped_files"][:5]:
                prompt_parts.append(f"- {file_info.get('file')}: {file_info.get('reason')}")
        prompt_parts.append("")
        
        # Historical matches
        if historical_matches:
            prompt_parts.append("## SIMILAR HISTORICAL DEFECTS")
            for match in historical_matches[:3]:
                prompt_parts.append(f"- {match.get('defect_id')} ({match.get('similarity_score', 0):.0%} similar)")
                prompt_parts.append(f"  Summary: {match.get('summary', 'N/A')}")
                if match.get('root_cause'):
                    prompt_parts.append(f"  Root Cause: {match.get('root_cause')}")
            prompt_parts.append("")
        
        # Analysis request
        prompt_parts.append("## ANALYSIS REQUEST")
        prompt_parts.append("""
Based on the information above (especially the DOMAIN KNOWLEDGE CONTEXT if pattern matches were found), please provide:
1. ROOT CAUSE: What is the most likely root cause of this defect?
2. EVIDENCE: What evidence supports this conclusion?
3. AFFECTED CODE: Which source files need to be fixed?
4. FIX RECOMMENDATION: What specific code changes are recommended?
5. CONFIDENCE: How confident are you in this analysis (0-100%)?
6. PREVENTIVE MEASURES: How can similar issues be prevented?

NOTE: If pattern matches were found in domain knowledge, use those as primary indicators for root cause.
""")
        
        return "\n".join(prompt_parts)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""
        return """You are an expert automotive infotainment software engineer specializing in:
- DLT (Diagnostic Log and Trace) log analysis
- Root Cause Analysis (RCA) for complex embedded systems
- Audio/Media subsystems, Bluetooth connectivity, CAN bus communication
- System boot and initialization sequences

IMPORTANT: You have access to DOMAIN KNOWLEDGE from the automotive infotainment knowledge base.
When "DOMAIN KNOWLEDGE CONTEXT" is provided with pattern matches, USE THOSE as primary indicators:
- Matched patterns have been verified against known root causes
- The "Likely Root Cause" from matched patterns should be your starting point
- Cross-reference pattern matches with DLT errors and historical defects

Analyze the provided defect information comprehensively and provide actionable insights.
Be specific about code files, functions, and exact fixes when possible.
Consider thread safety, resource management, and timing issues common in automotive systems."""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        result = {
            "raw_response": response,
            "root_cause": "",
            "evidence": [],
            "affected_files": [],
            "fix_recommendation": "",
            "confidence": 0.0,
            "preventive_measures": []
        }
        
        # Simple parsing - in production, use more sophisticated extraction
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'root cause' in line_lower:
                current_section = 'root_cause'
            elif 'evidence' in line_lower:
                current_section = 'evidence'
            elif 'affected' in line_lower and ('code' in line_lower or 'file' in line_lower):
                current_section = 'affected_files'
            elif 'fix' in line_lower or 'recommendation' in line_lower:
                current_section = 'fix'
            elif 'confidence' in line_lower:
                current_section = 'confidence'
            elif 'prevent' in line_lower:
                current_section = 'preventive'
            elif current_section and line.strip():
                if current_section == 'root_cause':
                    result["root_cause"] += line.strip() + " "
                elif current_section == 'evidence':
                    result["evidence"].append(line.strip())
                elif current_section == 'affected_files':
                    result["affected_files"].append(line.strip())
                elif current_section == 'fix':
                    result["fix_recommendation"] += line.strip() + " "
                elif current_section == 'confidence':
                    # Extract percentage
                    import re
                    match = re.search(r'(\d+)%?', line)
                    if match:
                        result["confidence"] = int(match.group(1)) / 100
                elif current_section == 'preventive':
                    result["preventive_measures"].append(line.strip())
        
        result["root_cause"] = result["root_cause"].strip()
        result["fix_recommendation"] = result["fix_recommendation"].strip()
        
        return result
    
    def _generate_mock_analysis(
        self, 
        defect_data: Dict[str, Any], 
        dlt_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate mock analysis when LLM is not available"""
        component = defect_data.get("component", "Unknown")
        summary = defect_data.get("summary", "")
        
        return {
            "root_cause": f"Based on DLT patterns and component mapping, the issue appears to be in the {component} module. Further LLM analysis is needed for precise root cause.",
            "evidence": dlt_analysis.get("errors", [])[:5],
            "affected_files": [f.get("file") for f in dlt_analysis.get("mapped_files", [])[:3]],
            "fix_recommendation": "Configure LLM API to get specific fix recommendations.",
            "confidence": 0.65,
            "preventive_measures": [
                "Add unit tests for error scenarios",
                "Implement timeout handling",
                "Add defensive null checks"
            ],
            "is_mock": True
        }
    
    def _generate_reports(
        self,
        defect_id: str,
        defect_data: Dict[str, Any],
        dlt_analysis: Dict[str, Any],
        source_mapping: Dict[str, Any],
        historical_matches: List[Dict[str, Any]],
        llm_analysis: Dict[str, Any],
        duplicate_info: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate both Markdown and HTML reports"""
        
        report_data = {
            "defect_id": defect_id,
            "defect_data": defect_data,
            "dlt_analysis": dlt_analysis,
            "source_mapping": source_mapping,
            "historical_matches": historical_matches,
            "llm_analysis": llm_analysis,
            "duplicate_info": duplicate_info,
            "timestamp": datetime.now().isoformat()
        }
        
        # Generate Markdown report
        md_content = self.report_generator.generate_markdown(report_data)
        md_filename = f"{defect_id}_rca.md"
        md_path = os.path.join(self.output_dir, md_filename)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # Generate HTML report using new professional format
        # Build RCA result structure for HTML generator
        rca_result = {
            "defect_id": defect_id,
            "status": "completed",
            "duration_seconds": 0,  # Will be updated by caller
            "stages": {
                "dlt_analysis": {"status": "completed", "data": dlt_analysis, "duration": 0},
                "source_mapping": {"status": "completed", "data": source_mapping, "duration": 0},
                "historical_match": {"status": "completed", "data": {"matches": historical_matches}, "duration": 0},
                "llm_analysis": {"status": "completed", "data": llm_analysis, "duration": 0}
            }
        }
        
        html_content = generate_rca_html_report(rca_result, defect_data)
        html_filename = f"{defect_id}_rca.html"
        html_path = os.path.join(self.output_dir, html_filename)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Reports generated: {md_path}, {html_path}")
        
        return {
            "markdown": {"path": md_path, "filename": md_filename, "content": md_content},
            "html": {"path": html_path, "filename": html_filename, "content": html_content}
        }
    
    def _update_jira(
        self,
        defect_id: str,
        llm_analysis: Dict[str, Any],
        reports: Dict[str, Any],
        duplicate_info: Dict[str, Any],
        mark_duplicates: bool,
        defect_data: Dict[str, Any] = None,
        dlt_analysis: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Update JIRA with RCA results"""
        jira_result = {
            "comment_added": False,
            "attachments_uploaded": False,
            "duplicate_marked": False
        }
        
        if not self.jira_client:
            self.logger.warning("JIRA client not configured")
            return jira_result
        
        try:
            # Add RCA comment using summary.prompt.md format
            comment = self._format_jira_comment(
                llm_analysis, duplicate_info, defect_data, dlt_analysis
            )
            self.jira_client.add_comment(defect_id, comment)
            jira_result["comment_added"] = True
            self.logger.info(f"Added RCA comment to {defect_id}")
            
            # Upload attachments (MD and HTML reports)
            md_path = reports["markdown"]["path"]
            html_path = reports["html"]["path"]
            
            self.jira_client.add_attachment(defect_id, md_path)
            self.jira_client.add_attachment(defect_id, html_path)
            jira_result["attachments_uploaded"] = True
            self.logger.info(f"Uploaded reports to {defect_id}")
            
            # Mark duplicate if applicable
            if mark_duplicates and duplicate_info.get("is_duplicate"):
                duplicate_of = duplicate_info.get("duplicate_of")
                self.jira_client.link_duplicate(defect_id, duplicate_of)
                jira_result["duplicate_marked"] = True
                jira_result["duplicate_of"] = duplicate_of
                self.logger.info(f"Marked {defect_id} as duplicate of {duplicate_of}")
            
        except Exception as e:
            self.logger.error(f"JIRA update failed: {e}")
            jira_result["error"] = str(e)
        
        return jira_result
    
    def _format_jira_comment(
        self, 
        llm_analysis: Dict[str, Any], 
        duplicate_info: Dict[str, Any],
        defect_data: Dict[str, Any] = None,
        dlt_analysis: Dict[str, Any] = None
    ) -> str:
        """
        Format RCA results as JIRA comment using summary.prompt.md format
        
        Args:
            llm_analysis: LLM analysis results
            duplicate_info: Duplicate detection info
            defect_data: Original defect data
            dlt_analysis: DLT log analysis results
        """
        defect_data = defect_data or {}
        dlt_analysis = dlt_analysis or {}
        
        lines = []
        
        # Get values from analysis
        defect_id = defect_data.get("key", "Unknown")
        domain = defect_data.get("component", "Not_Assigned")
        timestamp = dlt_analysis.get("error_timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))
        root_cause = llm_analysis.get("root_cause", "Unable to determine")
        effect = llm_analysis.get("effect", "User-visible impact could not be determined from available logs.")
        fix_recommendation = llm_analysis.get("fix_recommendation", "Further investigation required.")
        confidence = llm_analysis.get("confidence", 0)
        affected_files = llm_analysis.get("affected_files", [])
        
        # ================================================
        # SUMMARY
        # ================================================
        lines.append("*Summary :*")
        lines.append(f"{domain} Pre-Analysis is done for {defect_id} with Error Timestamp at: {timestamp}.")
        lines.append("")
        lines.append("================================================")
        lines.append("")
        
        # ================================================
        # ROOT CAUSE / INITIAL FINDINGS
        # ================================================
        lines.append("*Rootcause/Initial findings* :")
        lines.append(root_cause)
        lines.append("")
        
        # ================================================
        # EFFECT
        # ================================================
        lines.append("*Effect* :")
        lines.append(effect)
        lines.append("")
        
        # ================================================
        # NEXT STEPS / DOMAIN
        # ================================================
        lines.append("*Next Steps/Domain* :")
        lines.append(f"Suggest assigning to {domain} domain for further investigation. {fix_recommendation}")
        lines.append("")
        
        # ================================================
        # REMARKS (Similar/Related Tickets)
        # ================================================
        lines.append("*Remarks* :")
        if duplicate_info.get("related_defects"):
            lines.append("|| Rank || Jira_Key || Similarity_score || Remark ||")
            for idx, related in enumerate(duplicate_info["related_defects"][:5], 1):
                similarity = related.get('similarity_score', 0)
                remark = "Potential duplicate" if similarity >= 0.90 else "Related issue"
                lines.append(f"| {idx} | [{related['defect_id']}] | {similarity:.0%} | {remark} |")
        else:
            lines.append("N/A")
        lines.append("")
        
        lines.append("================================================")
        lines.append("")
        
        # ================================================
        # ISSUE TIMING AND CLASSIFICATION
        # ================================================
        lines.append("*Issue Timing and Classification :*")
        issue_type = defect_data.get("issue_type", "defect")
        summary = defect_data.get("summary", "").lower()
        
        # Detect timing keywords
        timing = "runtime"
        if "boot" in summary or "coldboot" in summary:
            timing = "coldboot"
        elif "str" in summary:
            timing = "STR (Suspend-to-RAM)"
        elif "ota" in summary:
            timing = "after OTA update"
        
        # Detect defect type
        defect_type = "unknown issue"
        if "crash" in summary:
            defect_type = "crash"
        elif "anr" in summary:
            defect_type = "ANR"
        elif "reboot" in summary:
            defect_type = "unexpected reboot"
        elif "audio" in summary:
            defect_type = "audio issue"
        elif "display" in summary or "screen" in summary:
            defect_type = "display issue"
        
        lines.append(f"Issue is observed during {timing} and is classified as {defect_type}.")
        lines.append("")
        
        # ================================================
        # LOG FILES REFERRED
        # ================================================
        lines.append("*Log Files Referred :*")
        dlt_file = defect_data.get("dlt_attachment", "")
        if dlt_file:
            lines.append(f"- Exported DLTs: [^{dlt_file}]")
        else:
            lines.append("N/A")
        lines.append("")
        
        # ================================================
        # TESTED SOFTWARE VERSION
        # ================================================
        lines.append("*Tested software version:*")
        sw_version = defect_data.get("sw_version", dlt_analysis.get("sw_version", "N/A"))
        lines.append(sw_version)
        lines.append("")
        
        # ================================================
        # USED HW DETAILS
        # ================================================
        lines.append("*Used HW details :*")
        lines.append("N/A")
        lines.append("")
        
        lines.append("================================================")
        lines.append("")
        
        # ================================================
        # PRE-ANALYSIS
        # ================================================
        lines.append("*Pre-analysis :*")
        lines.append("")
        
        # DLT/Fishbone findings
        lines.append("Findings from DLT log analysis:")
        if dlt_analysis.get("errors"):
            for error in dlt_analysis["errors"][:5]:
                if isinstance(error, dict):
                    lines.append(f"- {error.get('message', str(error))[:100]}")
                else:
                    lines.append(f"- {str(error)[:100]}")
        else:
            lines.append("- N/A")
        lines.append("")
        
        # Evidence from LLM analysis
        lines.append("Findings from RCA analysis:")
        if llm_analysis.get("evidence"):
            for evidence in llm_analysis["evidence"][:5]:
                lines.append(f"- {str(evidence)[:100]}")
        else:
            lines.append("- N/A")
        lines.append("")
        
        # Affected source files
        if affected_files:
            lines.append("Affected source files:")
            for f in affected_files[:5]:
                lines.append(f"- {f}")
            lines.append("")
        
        # ================================================
        # CODE FIX PREVIEW (if available)
        # ================================================
        code_fixes = llm_analysis.get("code_fixes", [])
        if code_fixes:
            lines.append("================================================")
            lines.append("")
            lines.append("*Proposed Code Fix :*")
            lines.append("")
            
            for idx, fix in enumerate(code_fixes[:3], 1):
                file_path = fix.get("file_path", "Unknown file")
                old_content = fix.get("old_content", "")
                new_content = fix.get("new_content", "")
                description = fix.get("description", "Code fix")
                
                lines.append(f"*Fix {idx}: {file_path}*")
                lines.append(f"_{description}_")
                lines.append("")
                
                # Show old code (to be replaced)
                if old_content:
                    lines.append("{{color:red}}*BEFORE (Remove):*{{color}}")
                    lines.append("{code:java}")
                    # Truncate if too long
                    old_display = old_content[:500] + "..." if len(old_content) > 500 else old_content
                    lines.append(old_display)
                    lines.append("{code}")
                    lines.append("")
                
                # Show new code (replacement)
                if new_content:
                    lines.append("{{color:green}}*AFTER (Add):*{{color}}")
                    lines.append("{code:java}")
                    # Truncate if too long
                    new_display = new_content[:500] + "..." if len(new_content) > 500 else new_content
                    lines.append(new_display)
                    lines.append("{code}")
                    lines.append("")
                
                lines.append("----")
                lines.append("")
        
        lines.append("================================================")
        lines.append("")
        lines.append(f"_This summary was generated with the assistance of AI. (Confidence: {confidence:.0%})_")
        lines.append(f"_Generated by RCA Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        lines.append("_Generated by RCA Report Tool._")
        lines.append("")
        
        # ================================================
        # TOKEN CONSUMPTION METRICS (if available)
        # ================================================
        token_metrics = llm_analysis.get("token_metrics", {})
        if token_metrics:
            lines.append("================================================")
            lines.append("")
            lines.append("*Token Consumption Metrics :*")
            lines.append("")
            lines.append("|| Stage || Input Tokens || Output Tokens || Total ||")
            
            total_input = 0
            total_output = 0
            
            for stage_name, stage_tokens in token_metrics.get("by_stage", {}).items():
                inp = stage_tokens.get("input", 0)
                out = stage_tokens.get("output", 0)
                total = inp + out
                total_input += inp
                total_output += out
                lines.append(f"| {stage_name} | {inp:,} | {out:,} | {total:,} |")
            
            lines.append(f"| *TOTAL* | *{total_input:,}* | *{total_output:,}* | *{total_input + total_output:,}* |")
            lines.append("")
            
            # Cost estimate
            cost_eur = token_metrics.get("estimated_cost_eur", 0)
            if cost_eur > 0:
                lines.append(f"_Estimated cost: €{cost_eur:.4f}_")
            lines.append("")
        
        lines.append("================================================")
        
        return "\n".join(lines)
    
    def _format_pr_jira_comment(
        self,
        defect_id: str,
        pr_result: Dict[str, Any]
    ) -> str:
        """
        Format PR creation result as JIRA comment
        
        Args:
            defect_id: Defect ID
            pr_result: Result from apply_fix_and_create_pr()
        """
        lines = []
        
        lines.append("*Pull Request Created :*")
        lines.append("")
        lines.append("================================================")
        lines.append("")
        
        pr_info = pr_result.get("pr", {})
        pr_url = pr_info.get("url", "N/A")
        pr_number = pr_info.get("number", "N/A")
        branch = pr_result.get("branch", "N/A")
        commit = pr_result.get("commit", "N/A")
        
        lines.append(f"*PR Link:* [{pr_url}]")
        lines.append(f"*PR Number:* #{pr_number}")
        lines.append(f"*Branch:* {branch}")
        lines.append(f"*Commit:* {commit[:8] if commit and commit != 'N/A' else 'N/A'}")
        lines.append("")
        
        # Show fixes applied
        fixes_applied = pr_result.get("fixes_applied", [])
        if fixes_applied:
            lines.append("*Files Modified:*")
            for fix in fixes_applied:
                file_path = fix.get("file", "Unknown")
                description = fix.get("description", "Fix applied")
                lines.append(f"- {file_path}: {description}")
            lines.append("")
        
        # Show code changes
        lines.append("*Code Changes:*")
        lines.append("")
        
        for idx, fix in enumerate(fixes_applied[:3], 1):
            file_path = fix.get("file", "Unknown")
            old_content = fix.get("old_content", "")
            new_content = fix.get("new_content", "")
            
            if old_content or new_content:
                lines.append(f"*{idx}. {file_path}*")
                
                if old_content:
                    lines.append("{code:title=BEFORE (Removed)|borderStyle=solid|borderColor=#ff0000}")
                    old_display = old_content[:400] + "\n..." if len(old_content) > 400 else old_content
                    lines.append(old_display)
                    lines.append("{code}")
                
                if new_content:
                    lines.append("{code:title=AFTER (Added)|borderStyle=solid|borderColor=#00ff00}")
                    new_display = new_content[:400] + "\n..." if len(new_content) > 400 else new_content
                    lines.append(new_display)
                    lines.append("{code}")
                
                lines.append("")
        
        lines.append("================================================")
        lines.append("")
        lines.append(f"_PR created by RCA Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        lines.append("_Please review and merge the PR to apply the fix._")
        lines.append("")
        lines.append("================================================")
        
        return "\n".join(lines)
    
    def update_jira_with_pr(
        self,
        defect_id: str,
        pr_result: Dict[str, Any]
    ) -> bool:
        """
        Update JIRA ticket with PR creation details
        
        Args:
            defect_id: Defect ID
            pr_result: Result from apply_fix_and_create_pr()
            
        Returns:
            Success status
        """
        if not self.jira_client:
            self.logger.warning("JIRA client not configured")
            return False
        
        if not pr_result.get("success") and not pr_result.get("partial_success"):
            self.logger.warning("PR creation was not successful, skipping JIRA update")
            return False
        
        try:
            comment = self._format_pr_jira_comment(defect_id, pr_result)
            self.jira_client.add_comment(defect_id, comment)
            self.logger.info(f"Added PR details comment to {defect_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update JIRA with PR details: {e}")
            return False
    
    def list_defects(self) -> List[Dict[str, Any]]:
        """List all available defects"""
        defects_file = os.path.join(self.defects_dir, "jira_api_defects.json")
        if os.path.exists(defects_file):
            with open(defects_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("defects", [])
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get defect statistics"""
        defects = self.list_defects()
        historical = self.historical_matcher.load_historical()
        
        return {
            "current_defects": len(defects),
            "historical_defects": len(historical),
            "by_component": self._count_by_field(defects, "component"),
            "by_priority": self._count_by_field(defects, "priority"),
            "by_status": self._count_by_field(defects, "status")
        }
    
    def _count_by_field(self, items: List[Dict], field: str) -> Dict[str, int]:
        """Count items by field value"""
        counts = {}
        for item in items:
            value = item.get(field, "Unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts

    # ==========================================
    # CODE FIX & PR WORKFLOW
    # ==========================================
    
    def apply_fix_and_create_pr(
        self,
        defect_id: str,
        analysis_result: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Apply recommended fix to source code and create a Pull Request
        
        This method takes the analysis result (with affected_files and fix_recommendation)
        and automatically:
        1. Gets the code fix from LLM based on the recommendation
        2. Creates a fix branch
        3. Applies the fix to affected files
        4. Commits and pushes the changes
        5. Creates a PR on GitHub (uses GIT_REPO_URL from .env)
        
        Args:
            defect_id: Defect ID (e.g., SAM1-2001)
            analysis_result: RCA analysis result (will fetch if not provided)
            
        Returns:
            Dict with PR creation result
        """
        result = {
            "success": False,
            "defect_id": defect_id,
            "branch": None,
            "commit": None,
            "pr": None,
            "fixes_applied": [],
            "errors": []
        }
        
        # Validate Git client is configured
        if not self.git_client:
            result["errors"].append("Git client not configured. Call set_git_client() first.")
            self.logger.error(result["errors"][-1])
            return result
        
        if not self.git_client.is_connected():
            result["errors"].append("Git repository not connected. Check GIT_REPO_URL configuration.")
            self.logger.error(result["errors"][-1])
            return result
        
        # Get analysis result if not provided
        if not analysis_result:
            self.logger.info(f"Running RCA analysis for {defect_id}...")
            rca_result = self.analyze_defect(defect_id, from_jira=True, upload_to_jira=False)
            if rca_result.get("status") != "completed":
                result["errors"].append(f"RCA analysis failed: {rca_result.get('error', 'Unknown error')}")
                return result
            analysis_result = rca_result.get("stages", {}).get("llm_analysis", {}).get("data", {})
        
        # Extract fix information from analysis
        affected_files = analysis_result.get("affected_files", [])
        fix_recommendation = analysis_result.get("fix_recommendation", "")
        root_cause = analysis_result.get("root_cause", "")
        
        if not affected_files:
            result["errors"].append("No affected files identified in analysis. Cannot apply fix.")
            return result
        
        if not fix_recommendation:
            result["errors"].append("No fix recommendation provided. Cannot apply fix.")
            return result
        
        self.logger.info(f"Applying fix for {defect_id}...")
        self.logger.info(f"Affected files: {affected_files}")
        
        # Step 1: Generate actual code fix using LLM
        code_fixes = self._generate_code_fix(
            defect_id, affected_files, fix_recommendation, root_cause
        )
        
        if not code_fixes:
            result["errors"].append("Failed to generate code fixes. LLM may not be configured.")
            return result
        
        # Step 2: Create fix branch
        branch_name = self.git_client.create_fix_branch(defect_id)
        if not branch_name:
            result["errors"].append("Failed to create fix branch")
            return result
        result["branch"] = branch_name
        
        # Step 3: Apply fixes to each affected file
        files_fixed = []
        for fix in code_fixes:
            file_path = fix.get("file_path")
            old_content = fix.get("old_content")
            new_content = fix.get("new_content")
            
            if not all([file_path, old_content, new_content]):
                self.logger.warning(f"Skipping incomplete fix for {file_path}")
                continue
            
            if self.git_client.apply_fix(file_path, old_content, new_content):
                files_fixed.append(file_path)
                result["fixes_applied"].append({
                    "file": file_path,
                    "description": fix.get("description", "Code fix applied"),
                    "old_content": old_content,
                    "new_content": new_content
                })
                self.logger.info(f"Applied fix to {file_path}")
            else:
                self.logger.warning(f"Failed to apply fix to {file_path}")
        
        if not files_fixed:
            result["errors"].append("No fixes could be applied to files")
            return result
        
        # Step 4: Commit changes
        commit_message = self._generate_commit_message(defect_id, root_cause, files_fixed)
        commit_hash = self.git_client.commit_fix(defect_id, commit_message, files_fixed)
        
        if not commit_hash:
            result["errors"].append("Failed to commit changes")
            return result
        result["commit"] = commit_hash
        
        # Step 5: Push branch
        if not self.git_client.push_branch(branch_name):
            result["errors"].append("Failed to push branch")
            return result
        
        # Step 6: Create PR on GitHub (auto-detects platform from GIT_REPO_URL)
        pr_description = self._generate_pr_description(
            defect_id, root_cause, fix_recommendation, result["fixes_applied"]
        )
        
        pr_info = self.git_client.create_pull_request(
            defect_id=defect_id,
            branch_name=branch_name,
            title=f"fix({defect_id}): {root_cause[:50]}..." if len(root_cause) > 50 else f"fix({defect_id}): {root_cause}",
            description=pr_description
        )
        
        if pr_info:
            result["pr"] = pr_info
            result["success"] = True
            self.logger.info(f"Successfully created PR for {defect_id}: {pr_info.get('url')}")
            
            # Step 7: Update JIRA with PR details and code changes
            if self.jira_client:
                self.update_jira_with_pr(defect_id, result)
        else:
            result["errors"].append("Failed to create PR (branch pushed successfully)")
            result["partial_success"] = True
        
        return result
    
    def _generate_code_fix(
        self,
        defect_id: str,
        affected_files: List[str],
        fix_recommendation: str,
        root_cause: str
    ) -> List[Dict[str, Any]]:
        """
        Generate actual code fix using LLM
        
        Args:
            defect_id: Defect ID
            affected_files: List of affected file paths
            fix_recommendation: Recommended fix from analysis
            root_cause: Identified root cause
            
        Returns:
            List of code fixes with old_content, new_content pairs
        """
        code_fixes = []
        
        if not self.llm_client:
            self.logger.error("LLM client not configured. Cannot generate code fixes.")
            return code_fixes
        
        for file_path in affected_files[:3]:  # Limit to 3 files
            # Clean file path (remove bullet points, etc.)
            clean_path = file_path.strip().lstrip('- ').strip()
            
            # Get current file content from Git
            file_content = self.git_client.get_file_content(clean_path)
            
            if not file_content:
                self.logger.warning(f"Could not read file: {clean_path}")
                continue
            
            # Ask LLM to generate the fix
            prompt = f"""You are fixing a bug in an automotive infotainment system.

## DEFECT: {defect_id}
## ROOT CAUSE: {root_cause}
## FIX RECOMMENDATION: {fix_recommendation}

## FILE TO FIX: {clean_path}

## CURRENT CODE:
```
{file_content[:3000]}  # First 3000 chars to avoid token limit
```

## TASK:
1. Identify the specific code section that needs to be fixed
2. Provide the EXACT old code that needs to be replaced (copy exactly from above)
3. Provide the NEW fixed code

## OUTPUT FORMAT (JSON):
```json
{{
    "old_content": "exact code to replace (multi-line OK)",
    "new_content": "fixed code (multi-line OK)",
    "description": "brief description of what was fixed"
}}
```

IMPORTANT: 
- The old_content MUST match exactly what's in the file
- Include enough context (3-5 lines before/after) for unique identification
- Only fix what's necessary for this defect
"""
            
            try:
                response = self.llm_client.analyze_text(
                    prompt=prompt,
                    system_message="You are an expert automotive software engineer. Generate precise code fixes in the exact JSON format requested."
                )
                
                # Parse JSON from response
                fix_data = self._parse_code_fix_response(response)
                
                if fix_data:
                    fix_data["file_path"] = clean_path
                    code_fixes.append(fix_data)
                    self.logger.info(f"Generated fix for {clean_path}")
                    
            except Exception as e:
                self.logger.error(f"Failed to generate fix for {clean_path}: {e}")
        
        return code_fixes
    
    def _parse_code_fix_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response to extract code fix JSON"""
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        
        if json_match:
            try:
                fix_data = json.loads(json_match.group(1))
                if "old_content" in fix_data and "new_content" in fix_data:
                    return fix_data
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON without code blocks
        try:
            # Find JSON-like structure
            json_match = re.search(r'\{[^{}]*"old_content"[^{}]*"new_content"[^{}]*\}', response, re.DOTALL)
            if json_match:
                fix_data = json.loads(json_match.group())
                return fix_data
        except (json.JSONDecodeError, AttributeError):
            pass
        
        self.logger.warning("Could not parse code fix from LLM response")
        return None
    
    def _generate_commit_message(
        self, 
        defect_id: str, 
        root_cause: str, 
        files_fixed: List[str]
    ) -> str:
        """Generate a descriptive commit message"""
        files_list = ", ".join([os.path.basename(f) for f in files_fixed[:3]])
        
        return f"""fix({defect_id}): {root_cause[:60]}

Root Cause: {root_cause}

Files Modified:
- {chr(10).join(['- ' + f for f in files_fixed])}

Automated fix generated by RCA Agent.
"""
    
    def _generate_pr_description(
        self,
        defect_id: str,
        root_cause: str,
        fix_recommendation: str,
        fixes_applied: List[Dict[str, Any]]
    ) -> str:
        """Generate PR description with analysis details"""
        files_section = "\n".join([
            f"- `{fix['file']}`: {fix.get('description', 'Fix applied')}"
            for fix in fixes_applied
        ])
        
        return f"""## Summary
Automated fix for defect **{defect_id}** generated by RCA Agent.

## Root Cause Analysis
{root_cause}

## Fix Recommendation
{fix_recommendation}

## Changes Made
{files_section}

## Related
- Defect: {defect_id}
- Generated by: RCA Agent

## Testing Checklist
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Code review completed

---
*This PR was automatically generated by the RCA Agent based on root cause analysis.*
"""
    
    def analyze_and_fix(
        self,
        defect_id: str,
        from_jira: bool = True,
        upload_to_jira: bool = True,
        create_pr: bool = True
    ) -> Dict[str, Any]:
        """
        Complete workflow: Analyze defect → Generate fix → Create PR
        
        This is the main entry point for end-to-end automated RCA and fix.
        Uses the GitHub repo configured in GIT_REPO_URL for PR creation.
        
        Args:
            defect_id: Defect ID (e.g., SAM1-2001)
            from_jira: If True, fetch defect from JIRA
            upload_to_jira: If True, upload reports to JIRA
            create_pr: If True, create PR with fix
            
        Returns:
            Complete result with analysis and PR info
        """
        result = {
            "defect_id": defect_id,
            "analysis": None,
            "pr_result": None,
            "success": False,
            "errors": []
        }
        
        # Step 1: Run RCA analysis
        self.logger.info(f"Step 1: Running RCA analysis for {defect_id}...")
        rca_result = self.analyze_defect(
            defect_id, 
            from_jira=from_jira, 
            upload_to_jira=upload_to_jira
        )
        result["analysis"] = rca_result
        
        if rca_result.get("status") != "completed":
            result["errors"].append(f"RCA analysis failed: {rca_result.get('error', 'Unknown')}")
            return result
        
        # Step 2: Create PR with fix (if enabled)
        if create_pr:
            self.logger.info(f"Step 2: Creating PR with fix for {defect_id}...")
            analysis_data = rca_result.get("stages", {}).get("llm_analysis", {}).get("data", {})
            
            pr_result = self.apply_fix_and_create_pr(
                defect_id=defect_id,
                analysis_result=analysis_data
            )
            result["pr_result"] = pr_result
            
            if pr_result.get("success"):
                result["success"] = True
                self.logger.info(f"Complete workflow finished for {defect_id}")
                self.logger.info(f"PR URL: {pr_result.get('pr', {}).get('url', 'N/A')}")
            else:
                result["errors"].extend(pr_result.get("errors", []))
                if pr_result.get("partial_success"):
                    result["partial_success"] = True
        else:
            result["success"] = True
        
        return result
