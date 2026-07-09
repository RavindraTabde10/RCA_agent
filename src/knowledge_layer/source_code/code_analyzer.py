"""
Code Analyzer - Analyzes source code for issues
"""

from typing import Dict, Any, List, Optional
import os
import logging


class CodeAnalyzer:
    """Analyzes source code for potential issues"""
    
    def __init__(self, repo_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.repo_path = repo_path
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a specific file
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            Analysis results
        """
        self.logger.info(f"Analyzing file: {file_path}")
        
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        results = {
            "file": file_path,
            "issues": [],
            "complexity": 0,
            "lines_of_code": 0,
            "functions": [],
            "classes": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            results["lines_of_code"] = len(content.splitlines())
            
            # Perform static analysis
            results["issues"] = self._static_analysis(content, file_path)
            
            # Calculate complexity
            results["complexity"] = self._calculate_complexity(content)
            
            # Extract functions and classes
            results["functions"] = self._extract_functions(content)
            results["classes"] = self._extract_classes(content)
            
        except Exception as e:
            self.logger.error(f"Error analyzing file: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def _static_analysis(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Perform static analysis on code"""
        issues = []
        
        # Check for common issues
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            # Check for TODO/FIXME comments
            if "TODO" in line or "FIXME" in line:
                issues.append({
                    "type": "todo",
                    "line": i,
                    "message": "TODO/FIXME comment found",
                    "severity": "low"
                })
            
            # Check for print/console statements (might indicate debugging code)
            if "print(" in line or "console.log" in line:
                issues.append({
                    "type": "debug_statement",
                    "line": i,
                    "message": "Debug statement found",
                    "severity": "low"
                })
        
        return issues
    
    def _calculate_complexity(self, content: str) -> int:
        """Calculate code complexity (simplified)"""
        # Simplified cyclomatic complexity
        complexity = 1  # Base complexity
        
        # Count decision points
        complexity += content.count("if ")
        complexity += content.count("elif ")
        complexity += content.count("else:")
        complexity += content.count("for ")
        complexity += content.count("while ")
        complexity += content.count("case ")
        complexity += content.count("&&")
        complexity += content.count("||")
        
        return complexity
    
    def _extract_functions(self, content: str) -> List[str]:
        """Extract function names from code"""
        import re
        functions = []
        
        # Python functions
        python_pattern = r'def\s+(\w+)\s*\('
        functions.extend(re.findall(python_pattern, content))
        
        # JavaScript/TypeScript functions
        js_pattern = r'function\s+(\w+)\s*\('
        functions.extend(re.findall(js_pattern, content))
        
        return list(set(functions))
    
    def _extract_classes(self, content: str) -> List[str]:
        """Extract class names from code"""
        import re
        classes = []
        
        # Python classes
        python_pattern = r'class\s+(\w+)\s*[\(:]'
        classes.extend(re.findall(python_pattern, content))
        
        # JavaScript/TypeScript classes
        js_pattern = r'class\s+(\w+)\s*[{]'
        classes.extend(re.findall(js_pattern, content))
        
        return list(set(classes))
    
    def find_related_code(
        self,
        error_message: str,
        stack_trace: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find code related to an error
        
        Args:
            error_message: Error message
            stack_trace: Optional stack trace
            
        Returns:
            List of related code locations
        """
        related = []
        
        if stack_trace:
            for trace_line in stack_trace:
                # Extract file and line number from stack trace
                location = self._parse_stack_trace_line(trace_line)
                if location:
                    related.append(location)
        
        return related
    
    def _parse_stack_trace_line(self, trace_line: str) -> Optional[Dict[str, Any]]:
        """Parse a line from stack trace"""
        import re
        
        # Try to extract file and line number
        # Example: "  File \"main.py\", line 42, in <module>"
        pattern = r'File "([^"]+)", line (\d+)'
        match = re.search(pattern, trace_line)
        
        if match:
            return {
                "file": match.group(1),
                "line": int(match.group(2)),
                "trace": trace_line
            }
        
        return None
    
    def analyze_repository(self, extensions: List[str] = None) -> Dict[str, Any]:
        """
        Analyze entire repository
        
        Args:
            extensions: File extensions to analyze (e.g., ['.py', '.js'])
            
        Returns:
            Repository-wide analysis
        """
        if not self.repo_path:
            return {"error": "No repository path configured"}
        
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.java', '.cpp']
        
        results = {
            "total_files": 0,
            "total_lines": 0,
            "total_issues": 0,
            "by_file": []
        }
        
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    file_results = self.analyze_file(file_path)
                    
                    results["total_files"] += 1
                    results["total_lines"] += file_results.get("lines_of_code", 0)
                    results["total_issues"] += len(file_results.get("issues", []))
                    results["by_file"].append(file_results)
        
        return results
