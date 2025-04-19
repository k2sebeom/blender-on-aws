import streamlit as st
from streamlit_extras.stateful_button import button
import argparse

from src.config.config_loader import ConfigLoader
from src.services.workspace_service import WorkspaceService
from src.services.blender_service import BlenderService

# Initialize session state for render logs
if "stdout" not in st.session_state:
    st.session_state.stdout = ""
if "stderr" not in st.session_state:
    st.session_state.stderr = ""
if "is_rendering" not in st.session_state:
    st.session_state.is_rendering = False

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

# Header
st.title("🎨 Render")
st.markdown(
    "Upload your .blend file and we'll render it for you! View job history in the sidebar."
)

# File upload section
with st.container():
    # Display max file size from config
    if config and "workspace" in config and "max_upload_size" in config["workspace"]:
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

        # Submit button - disabled while rendering
        if (
            button(
                "Start Rendering",
                key="render_button",
                disabled=st.session_state.is_rendering,
            )
            and is_valid
        ):
            # Set rendering state to True
            st.session_state.is_rendering = True
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
                        file_bytes, uploaded_file.name, run_dir
                    )

                    st.success(f"File stored successfully at: {stored_file}")

                    # Start rendering process
                    with st.spinner("Rendering your file..."):
                        # Initialize blender service
                        blender_service = BlenderService(
                            workspace_service.get_workspace_path()
                        )

                        # Render the file and get outputs
                        rendered_files, stdout, stderr = (
                            blender_service.render_blend_file(
                                stored_file, run_dir, frames_input
                            )
                        )

                        # Store the logs in session state
                        st.session_state.stdout = stdout
                        st.session_state.stderr = stderr

                        st.success("Rendering completed successfully!")

                        # Show expandable section with stdout/stderr tabs
                        with st.expander("View Render Logs"):
                            tab1, tab2 = st.tabs(["Standard Output", "Standard Error"])
                            with tab1:
                                st.text_area("stdout", value=stdout, height=300)
                            with tab2:
                                st.text_area("stderr", value=stderr, height=300)

                        # Display rendered images in a 3-column grid
                        st.subheader("📥 Rendered Files")
                        cols = st.columns(3)
                        for idx, render_file in enumerate(rendered_files):
                            # Read the PNG file
                            with open(render_file, "rb") as f:
                                image_bytes = f.read()

                            # Display the image in the appropriate column
                            with cols[idx % 3]:
                                st.image(
                                    image_bytes,
                                    caption=f"Frame {idx + 1}",
                                    use_container_width=True,
                                )
                                # Add download button for each frame
                                st.download_button(
                                    label=f"Download Frame {idx + 1}",
                                    data=image_bytes,
                                    file_name=render_file.name,
                                    mime="image/png",
                                )

                except Exception as e:
                    st.error(f"Error processing file: {e}")
                    st.stop()
                finally:
                    # Reset rendering state
                    st.session_state.is_rendering = False

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit")
