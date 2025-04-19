import streamlit as st
import argparse
from src.config.config_loader import ConfigLoader
from src.services.workspace_service import WorkspaceService

def initialize_app(description="Blender Online Renderer"):
    """Initialize configuration and workspace for the application.
    
    Args:
        description (str): Description for the argument parser
        
    Returns:
        tuple: (config, workspace_service) if successful, otherwise calls st.stop()
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )
    args = parser.parse_args()

    # Load configuration
    config = ConfigLoader.load_config(args.config)

    # Initialize workspace
    if config:
        workspace_service = WorkspaceService(config)
        if not workspace_service.initialize_workspace():
            st.error(
                "Failed to initialize workspace. Please check the configuration and permissions."
            )
            st.stop()
        return config, workspace_service
    
    st.error("Failed to load configuration.")
    st.stop()
