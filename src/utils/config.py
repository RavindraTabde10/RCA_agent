"""
Config - Configuration management
"""

import yaml
import os
import re
from typing import Dict, Any, Optional
import logging


def substitute_env_variables(config: Any) -> Any:
    """
    Recursively substitute ${VAR} placeholders with environment variables
    
    Args:
        config: Configuration value (can be dict, list, str, etc.)
        
    Returns:
        Configuration with substituted values
    """
    if isinstance(config, dict):
        return {key: substitute_env_variables(value) for key, value in config.items()}
    elif isinstance(config, list):
        return [substitute_env_variables(item) for item in config]
    elif isinstance(config, str):
        # Match ${VAR_NAME} pattern
        pattern = r'\$\{([^}]+)\}'
        
        def replacer(match):
            var_name = match.group(1)
            # Handle naming variations (JIRA_URL vs JIRA_BASE_URL, etc.)
            value = os.getenv(var_name)
            if value is None and var_name == 'JIRA_URL':
                value = os.getenv('JIRA_BASE_URL')
            if value is None and var_name == 'JIRA_PROJECT_KEY':
                value = os.getenv('JIRA_TICKET_KEY')
            return value if value is not None else match.group(0)
        
        return re.sub(pattern, replacer, config)
    else:
        return config


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return get_default_config()
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Substitute environment variables
        config = substitute_env_variables(config)
        
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Get default configuration"""
    return {
        "app": {
            "name": "RCA Agent",
            "version": "0.1.0",
            "log_level": "INFO"
        },
        "agents": {
            "log_agent": {
                "enabled": True
            },
            "code_agent": {
                "enabled": True
            },
            "pattern_agent": {
                "enabled": True
            }
        },
        "llm": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "integrations": {
            "jira": {
                "enabled": False,
                "url": ""
            },
            "git": {
                "enabled": False,
                "repo_path": ""
            }
        },
        "output": {
            "default_format": "text",
            "save_to_file": True,
            "output_dir": "output"
        }
    }


def save_config(config: Dict[str, Any], config_path: str):
    """Save configuration to file"""
    logger = logging.getLogger(__name__)
    
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Saved configuration to {config_path}")
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get configuration value using dot notation
    
    Args:
        config: Configuration dictionary
        key_path: Path to key (e.g., "agents.log_agent.enabled")
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    keys = key_path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value
