import streamlit as st
from streamlit_extras.stateful_button import button
import time
import argparse

from src.config.config_loader import ConfigLoader
from src.services.workspace_service import WorkspaceService

# Parse command line arguments
parser = argparse.ArgumentParser(description="Blender Online Renderer")
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

# Set page config
st.set_page_config(page_title="Blender Online Renderer", page_icon="🎨", layout="wide")

# Add custom CSS
st.markdown(
    """
    <style>
    .main {
        padding: 2rem;
    }
    .stProgress > div > div > div > div {
        background-color: #00cc00;
    }
    .upload-status {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success {
        background-color: #d4edda;
        color: #155724;
    }
    .error {
        background-color: #f8d7da;
        color: #721c24;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def main(config):
    # Header
    st.title("🎨 Blender Online Renderer")
    st.markdown("Upload your .blend file and we'll render it for you!")

    # File upload section
    with st.container():
        # Display max file size from config
        if (
            config
            and "workspace" in config
            and "max_upload_size" in config["workspace"]
        ):
            st.info(f"Maximum upload size: {config['workspace']['max_upload_size']} MB")

        # Configuration inputs
        job_name = st.text_input(
            "Job Name", placeholder="Enter a name for your rendering job"
        )
        frames_input = st.text_input(
            "Frame Range",
            placeholder="Single number (e.g., 1) or range (e.g., 1-100)",
            value=1,
        )

        st.subheader("📤 Upload Your File")
        uploaded_file = st.file_uploader("Choose a .blend file", type=["blend"])

        if uploaded_file:
            # Validate inputs
            is_valid = True
            if not job_name:
                st.error("Please enter a job name")
                is_valid = False

            if not frames_input:
                st.error("Please enter frame range")
                is_valid = False
            else:
                # Validate frame range format
                if "-" in frames_input:
                    try:
                        start, end = map(int, frames_input.split("-"))
                        if start >= end:
                            st.error("Start frame must be less than end frame")
                            is_valid = False
                    except ValueError:
                        st.error(
                            "Invalid frame range format. Use either a single number or start-end format"
                        )
                        is_valid = False
                else:
                    try:
                        frame = int(frames_input)
                        if frame < 1:
                            st.error("Frame number must be positive")
                            is_valid = False
                    except ValueError:
                        st.error("Invalid frame number")
                        is_valid = False

            # Submit button
            if button("Start Rendering", key="render_button") and is_valid:
                # Display confirmed settings
                st.info(f"""
                Rendering with the following settings:
                - Job Name: {job_name}
                - Frames: {frames_input}
                """)

                # Create job and run directories, store the file
                with st.spinner("Processing your file..."):
                    try:
                        # Create job directory
                        job_dir = workspace_service.create_job_directory(job_name)
                        
                        # Create run directory with timestamp
                        run_dir = workspace_service.create_run_directory(job_dir)
                        
                        # Store the uploaded file
                        file_bytes = uploaded_file.getvalue()
                        stored_file = workspace_service.store_uploaded_file(
                            file_bytes, 
                            uploaded_file.name, 
                            run_dir
                        )
                        
                        st.success(f"File stored successfully at: {stored_file}")
                    except Exception as e:
                        st.error(f"Error processing file: {e}")
                        st.stop()

                    # Show progress bar for rendering
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Simulate rendering progress (will be replaced with actual rendering)
                    for i in range(100):
                        time.sleep(
                            0.1
                        )  # This will be replaced with actual rendering progress
                        progress_bar.progress(i + 1)
                        status_text.text(f"Rendering: {i + 1}%")

                    # Show success message
                    st.success("Rendering completed successfully!")

                    # Download section
                    st.subheader("📥 Download Result")
                    st.markdown("""
                        Your rendered file is ready for download!
                        
                        Click the button below to download your rendered file:
                    """)
                    # This will be replaced with actual download link
                    st.download_button(
                        label="Download Rendered File",
                        data=b"placeholder",  # This will be replaced with actual file data
                        file_name="rendered_result.png",
                        mime="image/png",
                    )

    # Job History Section
    with st.container():
        st.subheader("📋 Recent Jobs")
        col1, col2, col3 = st.columns(3)

        # Sample job history (will be replaced with actual job tracking)
        with col1:
            st.metric("Active Jobs", "0")
        with col2:
            st.metric("Completed Today", "0")
        with col3:
            st.metric("Average Render Time", "0 min")

    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit")


if __name__ == "__main__":
    main(config)
