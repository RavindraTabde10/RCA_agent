"""
Source Mapper - Map DLT patterns and components to source code files

Maps:
- APP_IDs to source directories
- Error patterns to specific files
- Components to code modules
"""

import os
import logging
from typing import Dict, Any, List, Optional


class SourceMapper:
    """
    Maps DLT log information to source code files
    
    Uses component and pattern matching to identify
    which source files are likely involved in a defect.
    """
    
    # Component to directory/file mapping
    COMPONENT_FILE_MAP = {
        "AudioService": {
            "dir": "audio",
            "files": ["AudioManager.cpp", "AudioService.cpp", "AudioSession.cpp"],
            "main_file": "AudioManager.cpp"
        },
        "AudioMixer": {
            "dir": "audio",
            "files": ["AudioMixer.cpp", "MixerChannel.cpp", "AudioBuffer.cpp"],
            "main_file": "AudioMixer.cpp"
        },
        "MediaController": {
            "dir": "media",
            "files": ["MediaController.cpp", "MediaSession.cpp", "PlaybackManager.cpp"],
            "main_file": "MediaController.cpp"
        },
        "MediaPlayer": {
            "dir": "media",
            "files": ["MediaPlayer.cpp", "Decoder.cpp", "StreamHandler.cpp"],
            "main_file": "MediaPlayer.cpp"
        },
        "BluetoothManager": {
            "dir": "connectivity",
            "files": ["BluetoothManager.cpp", "BTDevice.cpp", "PairingManager.cpp"],
            "main_file": "BluetoothManager.cpp"
        },
        "BTHandsFree": {
            "dir": "connectivity",
            "files": ["BTHandsFree.cpp", "HFPProfile.cpp", "CallHandler.cpp"],
            "main_file": "BTHandsFree.cpp"
        },
        "BTA2DP": {
            "dir": "connectivity",
            "files": ["BTA2DP.cpp", "A2DPSink.cpp", "AudioCodec.cpp"],
            "main_file": "BTA2DP.cpp"
        },
        "WiFiManager": {
            "dir": "connectivity",
            "files": ["WiFiManager.cpp", "NetworkScanner.cpp", "Connection.cpp"],
            "main_file": "WiFiManager.cpp"
        },
        "SystemControl": {
            "dir": "system",
            "files": ["SystemManager.cpp", "StateController.cpp", "EventDispatcher.cpp"],
            "main_file": "SystemManager.cpp"
        },
        "BootManager": {
            "dir": "system",
            "files": ["BootManager.cpp", "InitSequence.cpp", "ServiceLoader.cpp"],
            "main_file": "BootManager.cpp"
        },
        "VehicleBus": {
            "dir": "communication",
            "files": ["VehicleBusController.cpp", "CANHandler.cpp", "MessageRouter.cpp"],
            "main_file": "VehicleBusController.cpp"
        },
        "CANController": {
            "dir": "communication",
            "files": ["CANController.cpp", "CANMessage.cpp", "SignalDecoder.cpp"],
            "main_file": "CANController.cpp"
        },
        "USBService": {
            "dir": "media",
            "files": ["USBMediaHandler.cpp", "USBScanner.cpp", "MediaIndexer.cpp"],
            "main_file": "USBMediaHandler.cpp"
        },
        "RadioTuner": {
            "dir": "media",
            "files": ["RadioTuner.cpp", "TunerDriver.cpp", "FrequencyManager.cpp"],
            "main_file": "RadioTuner.cpp"
        }
    }
    
    # Error pattern to file mapping
    PATTERN_FILE_MAP = {
        "timeout": ["common/TimeoutHandler.cpp", "common/Timer.cpp"],
        "memory": ["common/MemoryPool.cpp", "common/BufferManager.cpp"],
        "threading": ["common/ThreadPool.cpp", "common/Mutex.cpp", "common/Lock.cpp"],
        "null_reference": ["common/SafePtr.cpp", "common/Validator.cpp"],
        "connection": ["connectivity/ConnectionManager.cpp", "connectivity/RetryHandler.cpp"],
        "overflow": ["common/RingBuffer.cpp", "common/CircularQueue.cpp"],
        "exception": ["common/ExceptionHandler.cpp", "common/ErrorLogger.cpp"]
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Source Mapper
        
        Args:
            config: Configuration dictionary with source paths
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.src_path = config.get('paths', {}).get('src_dir', 'src')
    
    def map_to_source(self, dlt_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map DLT analysis results to source code files
        
        Args:
            dlt_analysis: Results from DLTAnalyzer
            
        Returns:
            Source mapping with files and reasons
        """
        result = {
            "mapped_files": [],
            "mapped_directories": [],
            "confidence": 0.0,
            "unmapped_components": []
        }
        
        seen_files = set()
        
        # Map components to files
        components = dlt_analysis.get("components", [])
        for component in components:
            if component in self.COMPONENT_FILE_MAP:
                mapping = self.COMPONENT_FILE_MAP[component]
                dir_path = mapping["dir"]
                
                if dir_path not in result["mapped_directories"]:
                    result["mapped_directories"].append(dir_path)
                
                # Add main file with high confidence
                main_file = f"{dir_path}/{mapping['main_file']}"
                if main_file not in seen_files:
                    result["mapped_files"].append({
                        "file": main_file,
                        "component": component,
                        "confidence": 0.9,
                        "reason": f"Primary source file for {component}"
                    })
                    seen_files.add(main_file)
                
                # Add related files with lower confidence
                for file in mapping["files"]:
                    full_path = f"{dir_path}/{file}"
                    if full_path not in seen_files:
                        result["mapped_files"].append({
                            "file": full_path,
                            "component": component,
                            "confidence": 0.7,
                            "reason": f"Related to {component}"
                        })
                        seen_files.add(full_path)
            else:
                result["unmapped_components"].append(component)
        
        # Map error patterns to files
        patterns = dlt_analysis.get("patterns", [])
        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            if pattern_type in self.PATTERN_FILE_MAP:
                for file in self.PATTERN_FILE_MAP[pattern_type]:
                    if file not in seen_files:
                        result["mapped_files"].append({
                            "file": file,
                            "pattern": pattern_type,
                            "confidence": 0.6,
                            "reason": f"Common handler for '{pattern_type}' issues"
                        })
                        seen_files.add(file)
        
        # Sort by confidence
        result["mapped_files"].sort(key=lambda x: x["confidence"], reverse=True)
        
        # Calculate overall confidence
        if result["mapped_files"]:
            result["confidence"] = sum(f["confidence"] for f in result["mapped_files"]) / len(result["mapped_files"])
        
        return result
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        Read source file content
        
        Args:
            file_path: Relative path to source file
            
        Returns:
            File content or None if not found
        """
        full_path = os.path.join(self.src_path, file_path)
        
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"Error reading {full_path}: {e}")
        
        return None
    
    def find_relevant_functions(
        self, 
        file_content: str, 
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Find functions in source that might be relevant
        
        Args:
            file_content: Source file content
            keywords: Keywords to search for
            
        Returns:
            List of potentially relevant functions
        """
        import re
        
        functions = []
        
        # Simple C++ function pattern
        func_pattern = r'(\w+)\s+(\w+)\s*\([^)]*\)\s*(?:const)?\s*{'
        
        for match in re.finditer(func_pattern, file_content):
            return_type = match.group(1)
            func_name = match.group(2)
            
            # Check if function name contains any keyword
            for keyword in keywords:
                if keyword.lower() in func_name.lower():
                    functions.append({
                        "name": func_name,
                        "return_type": return_type,
                        "keyword_match": keyword,
                        "position": match.start()
                    })
                    break
        
        return functions
    
    def get_code_context(
        self, 
        file_path: str, 
        error_message: str,
        context_lines: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        Get code context around potential error location
        
        Args:
            file_path: Source file path
            error_message: Error message to search for context
            context_lines: Number of context lines
            
        Returns:
            Code context dictionary
        """
        content = self.get_file_content(file_path)
        if not content:
            return None
        
        lines = content.split('\n')
        
        # Extract keywords from error message
        keywords = [w for w in error_message.split() if len(w) > 3]
        
        # Find lines with matching keywords
        matching_lines = []
        for i, line in enumerate(lines):
            for keyword in keywords:
                if keyword.lower() in line.lower():
                    matching_lines.append(i)
                    break
        
        if matching_lines:
            # Get context around first match
            center = matching_lines[0]
            start = max(0, center - context_lines // 2)
            end = min(len(lines), center + context_lines // 2)
            
            return {
                "file": file_path,
                "start_line": start + 1,
                "end_line": end + 1,
                "center_line": center + 1,
                "code": '\n'.join(lines[start:end]),
                "matching_keywords": keywords
            }
        
        return None
