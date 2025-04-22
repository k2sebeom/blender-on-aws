import yaml
import streamlit as st
from typing import Dict, Optional

class ConfigLoader:
    """Configuration loader class to handle YAML config loading and validation."""
    
    @staticmethod
    def load_config(config_path: str) -> Optional[Dict]:
        """
        Load configuration from YAML file.
        
        Args:
            config_path (str): Path to the YAML config file
            
        Returns:
            Optional[Dict]: Configuration dictionary or None if error occurs
        """
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            st.error(f"Error loading config file: {e}")
            return None
