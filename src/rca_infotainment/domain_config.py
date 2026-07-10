"""
Domain Configuration Module

Supports multi-industry RCA analysis with domain-specific:
- Log formats and parsers
- Terminology and keywords
- Analysis rules and patterns
- Report templates
- Component mappings

Usage:
    from rca_infotainment.domain_config import get_domain_config, DomainType
    
    config = get_domain_config()  # Uses RCA_DOMAIN from .env
    # or
    config = get_domain_config(DomainType.AUTOMOTIVE)
"""

import os
from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


class DomainType(Enum):
    """Supported industry domains."""
    AUTOMOTIVE = "automotive"
    TELECOM = "telecom"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    MANUFACTURING = "manufacturing"
    SOFTWARE = "software"
    CUSTOM = "custom"


@dataclass
class DomainConfig:
    """Domain-specific configuration."""
    
    domain: DomainType
    display_name: str
    description: str
    
    # Log parsing
    log_formats: List[str] = field(default_factory=list)
    log_parser: str = "generic"
    timestamp_formats: List[str] = field(default_factory=list)
    
    # Terminology
    error_keywords: List[str] = field(default_factory=list)
    warning_keywords: List[str] = field(default_factory=list)
    component_keywords: Dict[str, List[str]] = field(default_factory=dict)
    severity_mapping: Dict[str, str] = field(default_factory=dict)
    
    # Analysis
    common_root_causes: List[str] = field(default_factory=list)
    component_hierarchy: Dict[str, List[str]] = field(default_factory=dict)
    kpi_definitions: Dict[str, Dict] = field(default_factory=dict)
    
    # Report
    report_sections: List[str] = field(default_factory=list)
    terminology: Dict[str, str] = field(default_factory=dict)
    
    # LLM prompts
    system_prompt_suffix: str = ""
    analysis_context: str = ""


# ============================================================================
# Domain Configurations
# ============================================================================

AUTOMOTIVE_CONFIG = DomainConfig(
    domain=DomainType.AUTOMOTIVE,
    display_name="Automotive / Infotainment",
    description="Automotive infotainment and vehicle systems",
    
    log_formats=["dlt", "can", "lin", "flexray", "someip"],
    log_parser="dlt",
    timestamp_formats=[
        "%Y/%m/%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
        "%d.%m.%Y %H:%M:%S.%f"
    ],
    
    error_keywords=[
        "ERROR", "FATAL", "CRITICAL", "FAIL", "EXCEPTION", "CRASH",
        "TIMEOUT", "DEADLOCK", "SEGFAULT", "PANIC", "ASSERT"
    ],
    warning_keywords=[
        "WARNING", "WARN", "CAUTION", "DEGRADED", "SLOW", "RETRY",
        "KPI_FAIL", "THRESHOLD_EXCEEDED"
    ],
    
    component_keywords={
        "Media": ["MEDIA", "USB", "BT", "BLUETOOTH", "AUDIO", "VIDEO", "TUNER", "DAB", "FM", "AM"],
        "Navigation": ["NAVI", "NAV", "GPS", "MAP", "ROUTE", "GUIDANCE", "POI"],
        "Connectivity": ["WIFI", "4G", "5G", "LTE", "CELLULAR", "MODEM", "ANTENNA"],
        "HMI": ["HMI", "GUI", "DISPLAY", "TOUCH", "SCREEN", "RENDER", "ANIMATION"],
        "System": ["BOOT", "POWER", "STR", "RESUME", "SUSPEND", "INIT", "SHUTDOWN"],
        "CAN": ["CAN", "LIN", "FLEXRAY", "SOMEIP", "DIAG", "ECU"],
        "Voice": ["VOICE", "ASR", "TTS", "SPEECH", "ALEXA", "ASSISTANT"]
    },
    
    severity_mapping={
        "FATAL": "critical",
        "ERROR": "high",
        "WARNING": "medium",
        "INFO": "low",
        "DEBUG": "info"
    },
    
    common_root_causes=[
        "Thread synchronization issue",
        "Memory leak or corruption",
        "CAN bus timeout",
        "USB enumeration failure",
        "Audio focus conflict",
        "Display render timeout",
        "Boot sequence race condition",
        "Power state transition error",
        "Resource exhaustion",
        "Configuration mismatch"
    ],
    
    component_hierarchy={
        "Infotainment": ["Media", "Navigation", "Connectivity", "HMI", "Voice"],
        "Media": ["USB", "Bluetooth", "Tuner", "Streaming"],
        "System": ["Boot", "Power", "Memory", "Process"],
        "Vehicle": ["CAN", "LIN", "Diagnostics", "ECU"]
    },
    
    kpi_definitions={
        "STR": {"name": "Source-To-Render", "unit": "ms", "threshold": 200},
        "FMQ": {"name": "First Media Quality", "unit": "ms", "threshold": 500},
        "BOOT": {"name": "Cold Boot Time", "unit": "s", "threshold": 30},
        "RESUME": {"name": "Resume Time", "unit": "ms", "threshold": 3000}
    },
    
    report_sections=[
        "Executive Summary",
        "DLT Log Analysis",
        "Root Cause Analysis",
        "Component Impact",
        "Historical Patterns",
        "Fix Recommendations",
        "Code Changes",
        "Test Cases"
    ],
    
    terminology={
        "defect": "defect",
        "ticket": "JIRA ticket",
        "log": "DLT log",
        "component": "ECU/Module",
        "system": "Infotainment Unit"
    },
    
    system_prompt_suffix="""
You are analyzing automotive infotainment system logs (DLT format).
Focus on: timing issues, CAN/LIN communication, audio/video sync, boot sequences.
Key metrics: STR (Source-To-Render), FMQ (First Media Quality), boot times.
Consider: thread priorities, memory constraints, real-time requirements.
""",
    
    analysis_context="Automotive infotainment system running QNX/Linux"
)


TELECOM_CONFIG = DomainConfig(
    domain=DomainType.TELECOM,
    display_name="Telecommunications",
    description="Network and telecom infrastructure",
    
    log_formats=["syslog", "json", "pcap", "cdr"],
    log_parser="syslog",
    timestamp_formats=[
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%b %d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S"
    ],
    
    error_keywords=[
        "ERROR", "CRITICAL", "ALERT", "EMERGENCY", "FAILURE",
        "OUTAGE", "DISCONNECT", "DROPPED", "REJECTED"
    ],
    warning_keywords=[
        "WARNING", "DEGRADED", "CONGESTION", "RETRY", "TIMEOUT",
        "LATENCY", "PACKET_LOSS", "JITTER"
    ],
    
    component_keywords={
        "Core": ["EPC", "5GC", "MME", "SGW", "PGW", "AMF", "SMF", "UPF"],
        "RAN": ["ENODEB", "GNODEB", "RRU", "BBU", "ANTENNA", "CELL"],
        "Transport": ["MPLS", "IP", "VLAN", "BGP", "OSPF", "ROUTER", "SWITCH"],
        "Voice": ["SIP", "IMS", "VOLTE", "VONR", "RTP", "SBC", "MGW"],
        "Signaling": ["DIAMETER", "S1AP", "NGAP", "GTP", "PFCP", "NAS"]
    },
    
    common_root_causes=[
        "Network congestion",
        "Signaling storm",
        "Database sync failure",
        "License exhaustion",
        "Protocol mismatch",
        "Hardware failure",
        "Configuration error",
        "Capacity exceeded"
    ],
    
    kpi_definitions={
        "CSSR": {"name": "Call Setup Success Rate", "unit": "%", "threshold": 99.5},
        "CDR": {"name": "Call Drop Rate", "unit": "%", "threshold": 0.5},
        "LATENCY": {"name": "Network Latency", "unit": "ms", "threshold": 50},
        "THROUGHPUT": {"name": "Data Throughput", "unit": "Mbps", "threshold": 100}
    },
    
    terminology={
        "defect": "incident",
        "ticket": "trouble ticket",
        "log": "network log",
        "component": "network element",
        "system": "network"
    },
    
    system_prompt_suffix="""
You are analyzing telecommunications network logs.
Focus on: signaling flows, protocol exchanges, network topology.
Key metrics: CSSR, CDR, latency, throughput, availability.
Consider: redundancy, failover, capacity planning.
"""
)


HEALTHCARE_CONFIG = DomainConfig(
    domain=DomainType.HEALTHCARE,
    display_name="Healthcare / Medical",
    description="Healthcare systems and medical devices",
    
    log_formats=["hl7", "fhir", "dicom", "syslog", "json"],
    log_parser="generic",
    
    error_keywords=[
        "ERROR", "CRITICAL", "ALERT", "FAILURE", "EXCEPTION",
        "INVALID", "REJECTED", "VIOLATION", "BREACH"
    ],
    warning_keywords=[
        "WARNING", "CAUTION", "ABNORMAL", "OUT_OF_RANGE",
        "DELAYED", "PENDING", "RETRY"
    ],
    
    component_keywords={
        "EHR": ["EMR", "EHR", "PATIENT", "RECORD", "CHART", "ORDER"],
        "Lab": ["LAB", "RESULT", "SPECIMEN", "TEST", "LOINC"],
        "Imaging": ["PACS", "DICOM", "RADIOLOGY", "MRI", "CT", "XRAY"],
        "Pharmacy": ["RX", "MEDICATION", "DISPENSE", "NDC", "DRUG"],
        "Devices": ["MONITOR", "INFUSION", "VENTILATOR", "ECG", "VITALS"]
    },
    
    common_root_causes=[
        "Interface mapping error",
        "Data validation failure",
        "Authentication timeout",
        "HL7 parsing error",
        "Database constraint violation",
        "Network connectivity issue",
        "Certificate expiration",
        "Compliance violation"
    ],
    
    terminology={
        "defect": "incident",
        "ticket": "service request",
        "log": "audit log",
        "component": "system",
        "system": "clinical system"
    },
    
    system_prompt_suffix="""
You are analyzing healthcare system logs.
Focus on: HIPAA compliance, data integrity, patient safety.
Key concerns: PHI protection, audit trails, regulatory compliance.
Consider: HL7/FHIR standards, clinical workflows, interoperability.
"""
)


FINANCE_CONFIG = DomainConfig(
    domain=DomainType.FINANCE,
    display_name="Financial Services",
    description="Banking and financial systems",
    
    log_formats=["json", "csv", "fix", "swift", "syslog"],
    log_parser="generic",
    
    error_keywords=[
        "ERROR", "FAILED", "REJECTED", "DECLINED", "EXCEPTION",
        "FRAUD", "VIOLATION", "BREACH", "TIMEOUT"
    ],
    warning_keywords=[
        "WARNING", "SUSPICIOUS", "REVIEW", "PENDING", "DELAYED",
        "THRESHOLD", "LIMIT", "RETRY"
    ],
    
    component_keywords={
        "Trading": ["ORDER", "TRADE", "EXECUTION", "MARKET", "FIX", "ALGO"],
        "Payments": ["PAYMENT", "TRANSFER", "SWIFT", "ACH", "WIRE", "SEPA"],
        "Risk": ["RISK", "LIMIT", "EXPOSURE", "MARGIN", "COLLATERAL"],
        "Compliance": ["AML", "KYC", "SANCTION", "WATCHLIST", "AUDIT"],
        "Core Banking": ["ACCOUNT", "BALANCE", "LEDGER", "TRANSACTION"]
    },
    
    common_root_causes=[
        "Transaction timeout",
        "Insufficient funds",
        "Limit breach",
        "Connectivity failure",
        "Data mismatch",
        "Compliance rejection",
        "Market data delay",
        "Settlement failure"
    ],
    
    terminology={
        "defect": "incident",
        "ticket": "incident ticket",
        "log": "transaction log",
        "component": "system",
        "system": "platform"
    },
    
    system_prompt_suffix="""
You are analyzing financial system logs.
Focus on: transaction integrity, regulatory compliance, security.
Key concerns: PCI-DSS, SOX, data accuracy, audit trails.
Consider: real-time processing, settlement cycles, reconciliation.
"""
)


MANUFACTURING_CONFIG = DomainConfig(
    domain=DomainType.MANUFACTURING,
    display_name="Manufacturing / IoT",
    description="Industrial and manufacturing systems",
    
    log_formats=["opcua", "modbus", "mqtt", "json", "csv"],
    log_parser="generic",
    
    error_keywords=[
        "ERROR", "FAULT", "ALARM", "FAILURE", "STOP",
        "EMERGENCY", "CRITICAL", "OFFLINE"
    ],
    warning_keywords=[
        "WARNING", "CAUTION", "DEGRADED", "MAINTENANCE",
        "OUT_OF_SPEC", "THRESHOLD", "DRIFT"
    ],
    
    component_keywords={
        "PLC": ["PLC", "CONTROLLER", "LADDER", "IO", "REGISTER"],
        "SCADA": ["SCADA", "HMI", "HISTORIAN", "TAG", "ALARM"],
        "Sensors": ["SENSOR", "TEMPERATURE", "PRESSURE", "FLOW", "LEVEL"],
        "Actuators": ["MOTOR", "VALVE", "PUMP", "CONVEYOR", "ROBOT"],
        "Network": ["PROFINET", "ETHERNET", "MODBUS", "OPCUA", "MQTT"]
    },
    
    common_root_causes=[
        "Sensor calibration drift",
        "Communication timeout",
        "PLC firmware issue",
        "Power fluctuation",
        "Mechanical wear",
        "Configuration mismatch",
        "Network congestion",
        "Protocol incompatibility"
    ],
    
    terminology={
        "defect": "fault",
        "ticket": "work order",
        "log": "historian data",
        "component": "equipment",
        "system": "production line"
    },
    
    system_prompt_suffix="""
You are analyzing industrial/manufacturing system logs.
Focus on: equipment reliability, process control, safety.
Key metrics: OEE, downtime, cycle time, scrap rate.
Consider: real-time control, sensor accuracy, maintenance schedules.
"""
)


SOFTWARE_CONFIG = DomainConfig(
    domain=DomainType.SOFTWARE,
    display_name="Generic Software",
    description="General software applications",
    
    log_formats=["json", "syslog", "text", "csv"],
    log_parser="generic",
    
    error_keywords=[
        "ERROR", "EXCEPTION", "FATAL", "CRITICAL", "FAILURE",
        "CRASH", "PANIC", "ABORT", "TIMEOUT"
    ],
    warning_keywords=[
        "WARNING", "WARN", "DEPRECATED", "SLOW", "RETRY",
        "DEGRADED", "TIMEOUT"
    ],
    
    component_keywords={
        "Application": ["APP", "SERVICE", "HANDLER", "CONTROLLER", "API"],
        "Database": ["DB", "SQL", "QUERY", "CONNECTION", "POOL"],
        "Cache": ["REDIS", "MEMCACHED", "CACHE", "SESSION"],
        "Queue": ["KAFKA", "RABBITMQ", "QUEUE", "MESSAGE", "CONSUMER"],
        "Network": ["HTTP", "REST", "GRPC", "SOCKET", "CONNECTION"]
    },
    
    common_root_causes=[
        "Null pointer exception",
        "Memory leak",
        "Database connection exhausted",
        "Race condition",
        "Deadlock",
        "Configuration error",
        "API timeout",
        "Resource exhaustion"
    ],
    
    terminology={
        "defect": "bug",
        "ticket": "issue",
        "log": "application log",
        "component": "service",
        "system": "application"
    },
    
    system_prompt_suffix="""
You are analyzing software application logs.
Focus on: exceptions, performance, resource usage, API calls.
Key concerns: error handling, concurrency, scalability.
Consider: stack traces, request flows, dependency issues.
"""
)


# Domain registry
DOMAIN_CONFIGS: Dict[DomainType, DomainConfig] = {
    DomainType.AUTOMOTIVE: AUTOMOTIVE_CONFIG,
    DomainType.TELECOM: TELECOM_CONFIG,
    DomainType.HEALTHCARE: HEALTHCARE_CONFIG,
    DomainType.FINANCE: FINANCE_CONFIG,
    DomainType.MANUFACTURING: MANUFACTURING_CONFIG,
    DomainType.SOFTWARE: SOFTWARE_CONFIG,
}


# ============================================================================
# Public API
# ============================================================================

def get_domain_config(domain: Optional[DomainType] = None) -> DomainConfig:
    """
    Get domain configuration.
    
    Args:
        domain: Domain type. If None, reads from RCA_DOMAIN env var.
        
    Returns:
        DomainConfig for the specified domain.
    """
    if domain is None:
        domain_str = os.environ.get('RCA_DOMAIN', 'automotive').lower()
        try:
            domain = DomainType(domain_str)
        except ValueError:
            print(f"Warning: Unknown domain '{domain_str}', defaulting to SOFTWARE")
            domain = DomainType.SOFTWARE
    
    return DOMAIN_CONFIGS.get(domain, SOFTWARE_CONFIG)


def get_domain_type() -> DomainType:
    """Get current domain type from environment."""
    domain_str = os.environ.get('RCA_DOMAIN', 'automotive').lower()
    try:
        return DomainType(domain_str)
    except ValueError:
        return DomainType.SOFTWARE


def is_automotive() -> bool:
    """Check if running in automotive domain."""
    return get_domain_type() == DomainType.AUTOMOTIVE


def list_domains() -> List[Dict[str, str]]:
    """List all available domains."""
    return [
        {
            "id": d.value,
            "name": DOMAIN_CONFIGS[d].display_name,
            "description": DOMAIN_CONFIGS[d].description
        }
        for d in DomainType
        if d in DOMAIN_CONFIGS
    ]


# ============================================================================
# Convenience functions for common operations
# ============================================================================

def get_error_keywords() -> List[str]:
    """Get error keywords for current domain."""
    return get_domain_config().error_keywords


def get_warning_keywords() -> List[str]:
    """Get warning keywords for current domain."""
    return get_domain_config().warning_keywords


def get_component_keywords() -> Dict[str, List[str]]:
    """Get component keywords for current domain."""
    return get_domain_config().component_keywords


def get_common_root_causes() -> List[str]:
    """Get common root causes for current domain."""
    return get_domain_config().common_root_causes


def get_llm_system_suffix() -> str:
    """Get LLM system prompt suffix for current domain."""
    return get_domain_config().system_prompt_suffix


def get_terminology(term: str) -> str:
    """Get domain-specific term."""
    config = get_domain_config()
    return config.terminology.get(term, term)


# Print domain info on import if DEBUG
if os.environ.get('DEBUG_MODE', '').lower() == 'true':
    config = get_domain_config()
    print(f"[Domain] Loaded: {config.display_name} ({config.domain.value})")
