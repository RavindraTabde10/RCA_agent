"""
DLT Analyzer - Parse and analyze DLT (Diagnostic Log and Trace) logs

Extracts:
- Error messages
- Warning messages
- Components (APP_ID)
- Timestamps
- Patterns for root cause identification

Supports:
- Text-based DLT logs (human-readable)
- Binary DLT logs (AUTOSAR standard format)
"""

import re
import logging
import struct
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


class DLTAnalyzer:
    """
    Analyzer for DLT (Diagnostic Log and Trace) format logs
    
    DLT is a standard logging format used in automotive systems
    for debugging and tracing application behavior.
    """
    
    # APP_ID to Component mapping for infotainment systems
    APP_ID_COMPONENTS = {
        "AUDS": "AudioService",
        "AMIX": "AudioMixer",
        "MEDC": "MediaController",
        "MPLA": "MediaPlayer",
        "BTMG": "BluetoothManager",
        "BTHF": "BTHandsFree",
        "A2DP": "BTA2DP",
        "WIFM": "WiFiManager",
        "SYSC": "SystemControl",
        "BOOT": "BootManager",
        "DBUS": "DBusService",
        "NAVS": "NavigationService",
        "VBUS": "VehicleBus",
        "CANC": "CANController",
        "DIAG": "Diagnostics",
        "PWRM": "PowerManager",
        "TEMP": "TempMonitor",
        "USBS": "USBService",
        "TUNER": "RadioTuner",
        "RDS": "RDSDecoder",
        "CLIM": "ClimateControl"
    }
    
    # Error patterns to look for
    ERROR_PATTERNS = [
        (r'ERROR|FATAL|CRITICAL', 'error'),
        (r'WARN|WARNING', 'warning'),
        (r'timeout|timed.?out', 'timeout'),
        (r'failed|failure|fail', 'failure'),
        (r'null|nullptr|NULL', 'null_reference'),
        (r'memory|alloc|malloc|free', 'memory'),
        (r'mutex|lock|deadlock|blocked', 'threading'),
        (r'disconnected?|disconnect', 'connection'),
        (r'exception|crash', 'exception'),
        (r'overflow|underflow', 'overflow')
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize DLT Analyzer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    # =========================================================================
    # BINARY DLT PARSING (AUTOSAR Standard Format)
    # =========================================================================
    
    # DLT Message Type definitions
    DLT_TYPE_LOG = 0x00
    DLT_TYPE_APP_TRACE = 0x01
    DLT_TYPE_NW_TRACE = 0x02
    DLT_TYPE_CONTROL = 0x03
    
    # DLT Log Level definitions
    DLT_LOG_LEVELS = {
        0x00: "DEFAULT",
        0x01: "OFF",
        0x10: "FATAL",
        0x20: "ERROR",
        0x30: "WARN",
        0x40: "INFO",
        0x50: "DEBUG",
        0x60: "VERBOSE"
    }
    
    # DLT Magic number for storage header
    DLT_STORAGE_HEADER_PATTERN = b'DLT\x01'
    
    def analyze_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyze a DLT file (auto-detects binary vs text format)
        
        Args:
            file_path: Path to the DLT file
            
        Returns:
            Analysis results
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"DLT file not found: {file_path}")
            return self._empty_result()
        
        # Check if binary or text
        if self._is_binary_dlt(file_path):
            self.logger.info(f"Parsing binary DLT file: {file_path}")
            return self._parse_binary_dlt(file_path)
        else:
            self.logger.info(f"Parsing text DLT file: {file_path}")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return self.analyze(f.read())
    
    def _is_binary_dlt(self, file_path: Path) -> bool:
        """
        Check if a file is binary DLT format
        
        Binary DLT files typically start with 'DLT\x01' (storage header)
        or contain non-printable characters
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                
                # Check for DLT storage header magic
                if header == self.DLT_STORAGE_HEADER_PATTERN:
                    return True
                
                # Check for high ratio of non-printable characters
                f.seek(0)
                sample = f.read(1024)
                if not sample:
                    return False
                
                # Count non-printable, non-whitespace characters
                non_printable = sum(1 for b in sample if b < 32 and b not in (9, 10, 13))
                return (non_printable / len(sample)) > 0.1
                
        except Exception as e:
            self.logger.warning(f"Error checking file type: {e}")
            return False
    
    def _parse_binary_dlt(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse binary DLT file (AUTOSAR format)
        
        DLT Binary Format:
        ┌─────────────────────────────────────────────────────────────┐
        │ Storage Header (16 bytes) - Optional                        │
        │   - Pattern: 'DLT\x01' (4 bytes)                           │
        │   - Timestamp seconds (4 bytes)                             │
        │   - Timestamp microseconds (4 bytes)                        │
        │   - ECU ID (4 bytes)                                        │
        ├─────────────────────────────────────────────────────────────┤
        │ Standard Header (4 bytes minimum)                           │
        │   - Header Type (1 byte): UEH, MSBF, WEID, WSID, WTMS       │
        │   - Message Counter (1 byte)                                │
        │   - Length (2 bytes)                                        │
        │   - ECU ID (4 bytes) - if WEID set                         │
        │   - Session ID (4 bytes) - if WSID set                     │
        │   - Timestamp (4 bytes) - if WTMS set                      │
        ├─────────────────────────────────────────────────────────────┤
        │ Extended Header (10 bytes) - if UEH set                     │
        │   - Message Info (1 byte): VERB, MSTP, MTIN                │
        │   - Number of Args (1 byte)                                 │
        │   - Application ID (4 bytes)                                │
        │   - Context ID (4 bytes)                                    │
        ├─────────────────────────────────────────────────────────────┤
        │ Payload (variable)                                          │
        │   - Arguments with type info (if verbose)                   │
        │   - Raw data (if non-verbose)                               │
        └─────────────────────────────────────────────────────────────┘
        """
        result = self._empty_result()
        messages = []
        
        try:
            with open(file_path, 'rb') as f:
                file_size = os.path.getsize(file_path)
                msg_count = 0
                
                while f.tell() < file_size:
                    try:
                        msg = self._read_dlt_message(f)
                        if msg:
                            messages.append(msg)
                            msg_count += 1
                            
                            if msg_count >= 10000:  # Safety limit
                                self.logger.warning("Reached message limit (10000)")
                                break
                    except Exception as e:
                        # Try to recover by scanning for next DLT header
                        self.logger.debug(f"Parse error at offset {f.tell()}: {e}")
                        if not self._scan_to_next_message(f):
                            break
            
            # Convert binary messages to analysis format
            result = self._convert_messages_to_analysis(messages)
            result["total_lines"] = len(messages)
            result["format"] = "binary"
            
        except Exception as e:
            self.logger.error(f"Error parsing binary DLT: {e}")
        
        return result
    
    def _read_dlt_message(self, f) -> Optional[Dict[str, Any]]:
        """Read a single DLT message from binary file"""
        msg = {}
        
        # Check for storage header
        marker = f.read(4)
        if not marker:
            return None
        
        if marker == self.DLT_STORAGE_HEADER_PATTERN:
            # Read storage header
            storage_data = f.read(12)
            if len(storage_data) < 12:
                return None
            
            seconds, microseconds = struct.unpack('<II', storage_data[:8])
            ecu_id = storage_data[8:12].decode('ascii', errors='ignore').rstrip('\x00')
            
            msg["storage_timestamp"] = datetime.fromtimestamp(seconds + microseconds/1000000)
            msg["ecu_id"] = ecu_id
            
            # Read standard header
            marker = f.read(4)
            if not marker or len(marker) < 4:
                return None
        
        # Parse standard header
        if len(marker) < 4:
            return None
        
        header_type = marker[0]
        msg_counter = marker[1]
        length = struct.unpack('>H', marker[2:4])[0]
        
        # Header flags
        use_extended_header = bool(header_type & 0x01)  # UEH
        msbf = bool(header_type & 0x02)                  # Most Significant Byte First
        with_ecu_id = bool(header_type & 0x04)           # WEID
        with_session_id = bool(header_type & 0x08)       # WSID
        with_timestamp = bool(header_type & 0x10)        # WTMS
        
        msg["message_counter"] = msg_counter
        msg["length"] = length
        
        # Track bytes read for this message
        bytes_remaining = length - 4  # Already read 4 bytes of header
        
        # Read optional header fields
        if with_ecu_id and bytes_remaining >= 4:
            ecu = f.read(4)
            msg["ecu_id"] = ecu.decode('ascii', errors='ignore').rstrip('\x00')
            bytes_remaining -= 4
        
        if with_session_id and bytes_remaining >= 4:
            session = struct.unpack('>I', f.read(4))[0]
            msg["session_id"] = session
            bytes_remaining -= 4
        
        if with_timestamp and bytes_remaining >= 4:
            tmsp = struct.unpack('>I', f.read(4))[0]
            msg["timestamp_ticks"] = tmsp
            bytes_remaining -= 4
        
        # Read extended header
        if use_extended_header and bytes_remaining >= 10:
            ext_header = f.read(10)
            bytes_remaining -= 10
            
            msg_info = ext_header[0]
            num_args = ext_header[1]
            app_id = ext_header[2:6].decode('ascii', errors='ignore').rstrip('\x00')
            ctx_id = ext_header[6:10].decode('ascii', errors='ignore').rstrip('\x00')
            
            # Extract message type and log level
            verbose = bool(msg_info & 0x01)
            msg_type = (msg_info >> 1) & 0x07
            msg_type_info = (msg_info >> 4) & 0x0F
            
            msg["app_id"] = app_id
            msg["ctx_id"] = ctx_id
            msg["verbose"] = verbose
            msg["msg_type"] = msg_type
            msg["num_args"] = num_args
            
            # Map log level
            if msg_type == self.DLT_TYPE_LOG:
                log_level = msg_type_info << 4  # Shift to match DLT_LOG_LEVELS
                msg["level"] = self.DLT_LOG_LEVELS.get(log_level, "UNKNOWN")
            else:
                msg["level"] = "INFO"
        
        # Read payload
        if bytes_remaining > 0:
            payload = f.read(bytes_remaining)
            msg["payload_raw"] = payload
            msg["message"] = self._decode_payload(payload, msg.get("verbose", False), msg.get("num_args", 0))
        else:
            msg["message"] = ""
        
        return msg
    
    def _decode_payload(self, payload: bytes, verbose: bool, num_args: int) -> str:
        """
        Decode DLT payload to readable string
        
        Verbose mode: Each argument has type info prefix
        Non-verbose mode: Raw data, try to decode as string
        """
        if not payload:
            return ""
        
        if verbose and num_args > 0:
            # Parse verbose payload with type info
            return self._decode_verbose_payload(payload, num_args)
        else:
            # Try to decode as string
            return self._decode_non_verbose_payload(payload)
    
    def _decode_verbose_payload(self, payload: bytes, num_args: int) -> str:
        """Decode verbose DLT payload with argument type info"""
        parts = []
        offset = 0
        
        for _ in range(min(num_args, 20)):  # Safety limit
            if offset >= len(payload) - 4:
                break
            
            try:
                # Read type info (4 bytes)
                type_info = struct.unpack('>I', payload[offset:offset+4])[0]
                offset += 4
                
                # Type info bits
                type_len = type_info & 0x0F  # Type length code
                type_bool = bool(type_info & 0x10)
                type_sint = bool(type_info & 0x20)
                type_uint = bool(type_info & 0x40)
                type_floa = bool(type_info & 0x80)
                type_strg = bool(type_info & 0x200)
                type_rawd = bool(type_info & 0x400)
                
                if type_strg:
                    # String argument - read length then string
                    if offset + 2 > len(payload):
                        break
                    str_len = struct.unpack('>H', payload[offset:offset+2])[0]
                    offset += 2
                    if offset + str_len > len(payload):
                        str_len = len(payload) - offset
                    string_data = payload[offset:offset+str_len].decode('utf-8', errors='ignore').rstrip('\x00')
                    parts.append(string_data)
                    offset += str_len
                elif type_uint or type_sint:
                    # Integer argument
                    int_sizes = {1: 1, 2: 2, 3: 4, 4: 8}
                    int_size = int_sizes.get(type_len, 4)
                    if offset + int_size > len(payload):
                        break
                    if int_size == 1:
                        val = payload[offset]
                    elif int_size == 2:
                        val = struct.unpack('>H', payload[offset:offset+2])[0]
                    elif int_size == 4:
                        val = struct.unpack('>I', payload[offset:offset+4])[0]
                    else:
                        val = struct.unpack('>Q', payload[offset:offset+8])[0]
                    parts.append(str(val))
                    offset += int_size
                elif type_bool:
                    # Boolean
                    if offset < len(payload):
                        parts.append("true" if payload[offset] else "false")
                        offset += 1
                elif type_floa:
                    # Float
                    if type_len == 3 and offset + 4 <= len(payload):
                        val = struct.unpack('>f', payload[offset:offset+4])[0]
                        parts.append(f"{val:.3f}")
                        offset += 4
                    elif type_len == 4 and offset + 8 <= len(payload):
                        val = struct.unpack('>d', payload[offset:offset+8])[0]
                        parts.append(f"{val:.3f}")
                        offset += 8
                elif type_rawd:
                    # Raw data - just skip with length prefix
                    if offset + 2 <= len(payload):
                        raw_len = struct.unpack('>H', payload[offset:offset+2])[0]
                        offset += 2 + raw_len
                        parts.append(f"[RAW:{raw_len}bytes]")
                else:
                    # Unknown type, skip
                    break
                    
            except Exception:
                break
        
        return " ".join(parts)
    
    def _decode_non_verbose_payload(self, payload: bytes) -> str:
        """Decode non-verbose payload as string"""
        try:
            # Try UTF-8 first
            text = payload.decode('utf-8', errors='ignore')
            # Remove null bytes and control characters
            text = ''.join(c for c in text if c.isprintable() or c in '\n\t ')
            return text.strip()
        except Exception:
            # Fall back to hex representation for truly binary data
            return payload.hex()[:200]
    
    def _scan_to_next_message(self, f) -> bool:
        """Scan forward to find next DLT storage header"""
        chunk_size = 1024
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                return False
            
            idx = chunk.find(self.DLT_STORAGE_HEADER_PATTERN)
            if idx >= 0:
                # Found header, seek back to it
                f.seek(f.tell() - len(chunk) + idx)
                return True
        
        return False
    
    def _convert_messages_to_analysis(self, messages: List[Dict]) -> Dict[str, Any]:
        """Convert parsed binary messages to analysis format"""
        result = self._empty_result()
        
        seen_components = set()
        seen_app_ids = set()
        
        for i, msg in enumerate(messages):
            app_id = msg.get("app_id", "")
            level = msg.get("level", "INFO")
            message = msg.get("message", "")
            timestamp = msg.get("storage_timestamp")
            
            # Track APP_IDs and components
            if app_id:
                seen_app_ids.add(app_id)
                component = self.APP_ID_COMPONENTS.get(app_id, app_id)
                seen_components.add(component)
            
            # Track timestamps
            if timestamp:
                result["timestamps"].append(str(timestamp))
            
            # Classify by level
            if level in ("ERROR", "FATAL"):
                error_entry = {
                    "line": i + 1,
                    "level": level,
                    "app_id": app_id,
                    "ctx_id": msg.get("ctx_id", ""),
                    "component": self.APP_ID_COMPONENTS.get(app_id, "Unknown"),
                    "message": message,
                    "timestamp": str(timestamp) if timestamp else None
                }
                result["errors"].append(error_entry)
                
                comp = error_entry["component"]
                if comp not in result["component_errors"]:
                    result["component_errors"][comp] = []
                result["component_errors"][comp].append(error_entry)
                
            elif level == "WARN":
                result["warnings"].append({
                    "line": i + 1,
                    "level": level,
                    "app_id": app_id,
                    "message": message
                })
            
            # Detect patterns
            detected_patterns = self._detect_patterns(message)
            for pattern in detected_patterns:
                if pattern not in [p["type"] for p in result["patterns"]]:
                    result["patterns"].append({
                        "type": pattern,
                        "line": i + 1,
                        "message": message[:100]
                    })
        
        result["components"] = sorted(list(seen_components))
        result["app_ids"] = sorted(list(seen_app_ids))
        
        # Generate summary
        result["summary"] = {
            "error_count": len(result["errors"]),
            "warning_count": len(result["warnings"]),
            "component_count": len(result["components"]),
            "pattern_types": [p["type"] for p in result["patterns"]],
            "most_errors_component": self._get_top_component(result["component_errors"])
        }
        
        return result
    
    # =========================================================================
    # TEXT-BASED DLT PARSING (Original Implementation)
    # =========================================================================
    
    def analyze(self, dlt_content: str) -> Dict[str, Any]:
        """
        Analyze DLT log content
        
        Args:
            dlt_content: Raw DLT log text
            
        Returns:
            Analysis results with errors, warnings, components, etc.
        """
        if not dlt_content:
            return self._empty_result()
        
        lines = dlt_content.strip().split('\n')
        
        result = {
            "total_lines": len(lines),
            "errors": [],
            "warnings": [],
            "components": [],
            "app_ids": [],
            "timestamps": [],
            "patterns": [],
            "error_timeline": [],
            "component_errors": {},
            "summary": {}
        }
        
        seen_components = set()
        seen_app_ids = set()
        
        for i, line in enumerate(lines):
            parsed = self._parse_line(line)
            
            if parsed:
                # Track APP_IDs and components
                if parsed.get("app_id"):
                    app_id = parsed["app_id"]
                    seen_app_ids.add(app_id)
                    component = self.APP_ID_COMPONENTS.get(app_id, app_id)
                    seen_components.add(component)
                
                # Track timestamps
                if parsed.get("timestamp"):
                    result["timestamps"].append(parsed["timestamp"])
                
                # Classify message
                level = parsed.get("level", "").upper()
                message = parsed.get("message", "")
                
                if level in ("ERROR", "FATAL", "CRITICAL"):
                    error_entry = {
                        "line": i + 1,
                        "level": level,
                        "app_id": parsed.get("app_id"),
                        "component": self.APP_ID_COMPONENTS.get(parsed.get("app_id", ""), "Unknown"),
                        "message": message,
                        "timestamp": parsed.get("timestamp")
                    }
                    result["errors"].append(error_entry)
                    
                    # Track by component
                    comp = error_entry["component"]
                    if comp not in result["component_errors"]:
                        result["component_errors"][comp] = []
                    result["component_errors"][comp].append(error_entry)
                    
                elif level in ("WARN", "WARNING"):
                    result["warnings"].append({
                        "line": i + 1,
                        "level": level,
                        "app_id": parsed.get("app_id"),
                        "message": message
                    })
                
                # Detect patterns
                detected_patterns = self._detect_patterns(message)
                for pattern in detected_patterns:
                    if pattern not in [p["type"] for p in result["patterns"]]:
                        result["patterns"].append({
                            "type": pattern,
                            "line": i + 1,
                            "message": message[:100]
                        })
        
        result["components"] = sorted(list(seen_components))
        result["app_ids"] = sorted(list(seen_app_ids))
        
        # Generate summary
        result["summary"] = {
            "error_count": len(result["errors"]),
            "warning_count": len(result["warnings"]),
            "component_count": len(result["components"]),
            "pattern_types": [p["type"] for p in result["patterns"]],
            "most_errors_component": self._get_top_component(result["component_errors"])
        }
        
        return result
    
    def _parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single DLT log line"""
        if not line.strip():
            return None
        
        # DLT format patterns
        # Format 1: timestamp APP_ID LEVEL message
        # Format 2: [timestamp] [APP_ID] LEVEL: message
        # Format 3: timestamp | APP_ID | LEVEL | message
        
        patterns = [
            # Pattern 1: 2026-07-09 10:30:45.123 AUDS ERROR Audio buffer underrun
            r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[\.\d]*)\s+(\w{4})\s+(\w+)\s+(.*)$',
            
            # Pattern 2: [10:30:45] [AUDS] ERROR: Audio buffer underrun
            r'^\[([^\]]+)\]\s+\[(\w+)\]\s+(\w+):\s*(.*)$',
            
            # Pattern 3: 10:30:45.123 | AUDS | ERROR | Audio buffer underrun
            r'^([\d:\.]+)\s*\|\s*(\w+)\s*\|\s*(\w+)\s*\|\s*(.*)$',
            
            # Pattern 4: AUDS ERROR Audio buffer underrun
            r'^(\w{4})\s+(ERROR|WARN|WARNING|INFO|DEBUG|FATAL)\s+(.*)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 4:
                    return {
                        "timestamp": groups[0],
                        "app_id": groups[1].upper(),
                        "level": groups[2].upper(),
                        "message": groups[3]
                    }
                elif len(groups) == 3:
                    return {
                        "timestamp": None,
                        "app_id": groups[0].upper(),
                        "level": groups[1].upper(),
                        "message": groups[2]
                    }
        
        # Fallback: just check for keywords
        for keyword in ["ERROR", "WARN", "FATAL", "CRITICAL"]:
            if keyword in line.upper():
                return {
                    "timestamp": None,
                    "app_id": None,
                    "level": keyword,
                    "message": line
                }
        
        return None
    
    def _detect_patterns(self, message: str) -> List[str]:
        """Detect error patterns in a message"""
        patterns_found = []
        
        for pattern, pattern_type in self.ERROR_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                patterns_found.append(pattern_type)
        
        return patterns_found
    
    def _get_top_component(self, component_errors: Dict[str, List]) -> Optional[str]:
        """Get component with most errors"""
        if not component_errors:
            return None
        
        return max(component_errors.keys(), key=lambda k: len(component_errors[k]))
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "total_lines": 0,
            "errors": [],
            "warnings": [],
            "components": [],
            "app_ids": [],
            "timestamps": [],
            "patterns": [],
            "error_timeline": [],
            "component_errors": {},
            "summary": {
                "error_count": 0,
                "warning_count": 0,
                "component_count": 0,
                "pattern_types": [],
                "most_errors_component": None
            }
        }
    
    def get_error_summary(self, dlt_content: str) -> str:
        """Get a brief text summary of errors for LLM prompt"""
        analysis = self.analyze(dlt_content)
        
        lines = []
        lines.append(f"Total errors: {analysis['summary']['error_count']}")
        lines.append(f"Total warnings: {analysis['summary']['warning_count']}")
        lines.append(f"Components involved: {', '.join(analysis['components'])}")
        
        if analysis['patterns']:
            lines.append(f"Patterns detected: {', '.join(analysis['summary']['pattern_types'])}")
        
        if analysis['errors']:
            lines.append("\nTop errors:")
            for error in analysis['errors'][:5]:
                lines.append(f"  - [{error['component']}] {error['message'][:80]}")
        
        return "\n".join(lines)
