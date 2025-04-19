import streamlit as st
import json
from datetime import datetime

from src.services.blender_service import BlenderService
from src.utils.styles import get_common_styles
from src.utils.config_init import initialize_app

# Initialize session state
if "is_rendering" not in st.session_state:
    st.session_state.is_rendering = False

# Initialize app and get config/workspace service
config, workspace_service = initialize_app()

# Add custom CSS
st.markdown(get_common_styles(), unsafe_allow_html=True)

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
    
    # Render mode selection
    render_mode = st.radio(
        "Render Mode",
        options=["Still Frame", "Animation"],
        horizontal=True
    )
    
    # Frame inputs based on mode
    if render_mode == "Still Frame":
        frames_input = st.text_input(
            "Frame Range",
            placeholder="Single number (e.g., 1) or range (e.g., 1..100) or list (e.g., 1,2,3)",
            value=1,
        )
    else:  # Animation mode
        col1, col2 = st.columns(2)
        with col1:
            start_frame = st.number_input("Start Frame", min_value=1, value=1)
        with col2:
            end_frame = st.number_input("End Frame", min_value=start_frame, value=None)

    st.subheader("📤 Upload Your File")
    uploaded_file = st.file_uploader("Choose a .blend file", type=["blend"])

    if uploaded_file:
        # Validate inputs
        is_valid = True
        if not job_name:
            st.error("Please enter a job name")
            is_valid = False

        if render_mode == "Still Frame":
            if not frames_input:
                st.error("Please enter frame range")
                is_valid = False
            else:
                # Validate frame range format
                try:
                    for frame in map(int, frames_input.replace("..", ",").split(",")):
                        if frame < 1:
                            st.error("Frame number must be positive")
                            is_valid = False
                            break
                except ValueError:
                    st.error(
                        "Invalid frame range format. Use either a single number, start..end, or f,f,f format"
                    )
                    is_valid = False

        if "render_button" not in st.session_state:
            st.session_state.is_rendering = False

        def set_render_state(state: bool):
            st.session_state.is_rendering = state

        # Submit button - disabled while rendering
        if (
            st.button(
                "Start Rendering",
                key="render_button",
                on_click=set_render_state,
                args=(True,),
                disabled=st.session_state.is_rendering,
            )
            and is_valid
        ):
            # Display confirmed settings
            settings_info = f"""
            Rendering with the following settings:
            - Job Name: {job_name}
            - Mode: {render_mode}"""
            
            if render_mode == "Still Frame":
                settings_info += f"\n            - Frame: {frames_input}"
            else:
                settings_info += f"\n            - Start Frame: {start_frame}"
                if end_frame:
                    settings_info += f"\n            - End Frame: {end_frame}"
                
            st.info(settings_info)

            # Create job and run directories, store the file
            with st.spinner("Processing your file..."):
                try:
                    # Create job directory
                    job_dir = workspace_service.create_job_directory(job_name)

                    # Create run directory with timestamp
                    run_dir = workspace_service.create_run_directory(job_dir)

                    # Create initial metadata
                    meta = {
                        "created_time": datetime.now().isoformat(),
                        "mode": render_mode,
                        "source_file": uploaded_file.name,
                        "finished_time": None,
                        "num_files": 0,
                        "render_time": 0,
                    }
                    
                    if render_mode == "Still Frame":
                        meta["frame"] = frames_input
                    else:
                        meta["start_frame"] = start_frame
                        meta["end_frame"] = end_frame

                    # Write initial metadata
                    with open(run_dir / "meta.json", "w") as f:
                        json.dump(meta, f, indent=2)

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
                        mode = "still" if render_mode == "Still Frame" else "anim"
                        rendered_files, stdout, stderr = (
                            blender_service.render_blend_file(
                                stored_file, 
                                run_dir,
                                mode=mode,
                                start_frame=None if mode == "still" else start_frame,
                                end_frame=None if mode == "still" else end_frame,
                                frames_input=frames_input if mode == "still" else None,
                            )
                        )

                        # Update metadata with completion info
                        meta["finished_time"] = datetime.now().isoformat()
                        meta["num_files"] = len(rendered_files)
                        # Calculate render time in seconds
                        created_time = datetime.fromisoformat(meta["created_time"])
                        finished_time = datetime.fromisoformat(meta["finished_time"])
                        meta["render_time"] = (
                            finished_time - created_time
                        ).total_seconds()

                        # Write final metadata
                        with open(run_dir / "meta.json", "w") as f:
                            json.dump(meta, f, indent=2)

                        st.success("Rendering completed successfully!")

                        # Show expandable section with stdout/stderr tabs
                        with st.expander("View Render Logs"):
                            tab1, tab2 = st.tabs(["Standard Output", "Standard Error"])
                            with tab1:
                                st.text_area("stdout", value=stdout, height=300)
                            with tab2:
                                st.text_area("stderr", value=stderr, height=300)

                        # Display rendered output
                        st.subheader("📥 Rendered Files")
                        if mode == "still":
                            # Display rendered images in a 3-column grid
                            cols = st.columns(3)
                            for idx, (jpg_file, png_file) in enumerate(rendered_files):
                                # Read the render file
                                with open(png_file, "rb") as f:
                                    image_bytes = f.read()

                                # Display the image in the appropriate column
                                with cols[idx % 3]:
                                    st.image(
                                        jpg_file,
                                        caption=f"Frame {idx + 1}",
                                        use_container_width=True,
                                    )
                                    # Add download button for each frame
                                    st.download_button(
                                        label=f"Download Frame {idx + 1}",
                                        data=image_bytes,
                                        file_name=png_file.name,
                                        mime="image/png",
                                    )
                        else:  # Animation mode
                            cols = st.columns(2)
                            if rendered_files:
                                # Get the first (and only) video pair
                                src_vid, mp4_vid = rendered_files[0]
                                # Display the video
                                with cols[0]:
                                    st.video(str(mp4_vid))

                                # Add download button for the video
                                with open(mp4_vid, "rb") as f:
                                    st.download_button(
                                        label="Download Animation",
                                        data=f,
                                        file_name=mp4_vid.name,
                                        mime="video/mp4",
                                    )

                except Exception as e:
                    st.error(f"Error processing file: {e}")
                    st.stop()


# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit")
