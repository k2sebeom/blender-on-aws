import streamlit as st
import pandas as pd

from src.models.job import RenderMode
from src.workers.render_worker import RenderWorker
from src.utils.styles import get_common_styles
from src.utils.config_init import initialize_app

st.set_page_config(
    "Blender on AWS",
    layout="wide",
)

# Initialize session state
if "is_rendering" not in st.session_state:
    st.session_state.is_rendering = False

# Initialize app and get config/workspace service
config, workspace_service, db_service = initialize_app()

# Initialize render worker
if "render_worker" not in st.session_state:
    st.session_state.render_worker = RenderWorker.get_instance(workspace_service, db_service)
    if not st.session_state.render_worker.is_alive():
        st.session_state.render_worker.start()

# Add custom CSS
st.markdown(get_common_styles(), unsafe_allow_html=True)

cols = st.columns(3)

with cols[0]:
    # Header
    st.title("🎨 Render")
    st.markdown(
        "Upload your .blend file and we'll render it for you! View job history in the sidebar."
    )

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

        # Render mode selection
        render_mode: RenderMode = st.radio(
            "Render Mode", options=[RenderMode.still, RenderMode.anim], horizontal=True
        )

        # Frame inputs based on mode
        if render_mode == RenderMode.still:
            frame_range = st.text_input(
                "Frame Range",
                placeholder="Single number (e.g., 1) or range (e.g., 1..100) or list (e.g., 1,2,3)",
                value=1,
            )
        else:  # Animation mode
            col1, col2 = st.columns(2)
            with col1:
                start_frame = st.number_input("Start Frame", min_value=1, value=1)
            with col2:
                end_frame = st.number_input(
                    "End Frame", min_value=start_frame, value=None
                )

        st.subheader("📤 Upload Your File")
        uploaded_file = st.file_uploader("Choose a .blend file", type=["blend"])

        if uploaded_file:
            # Validate inputs
            is_valid = True
            if not job_name:
                st.error("Please enter a job name")
                is_valid = False

            if render_mode == RenderMode.still:
                if not frame_range:
                    st.error("Please enter frame range")
                    is_valid = False
                else:
                    # Validate frame range format
                    try:
                        for frame in map(
                            int, frame_range.replace("..", ",").split(",")
                        ):
                            if frame < 1:
                                st.error("Frame number must be positive")
                                is_valid = False
                                break
                    except ValueError:
                        st.error(
                            "Invalid frame range format. Use either a single number, start..end, or f,f,f format"
                        )
                        is_valid = False

            # Submit button - disabled while rendering
            if (
                st.button(
                    "Submit Job",
                    key="render_button",
                )
                and is_valid
            ):
                # Create job directories, store the file
                with st.spinner("Processing your file..."):
                    # try:
                    if render_mode == RenderMode.anim:
                        frame_range = (
                            "-".join([str(start_frame), str(end_frame)])
                            if end_frame
                            else str(start_frame)
                        )
                    # Create job entry
                    job = db_service.create_job(
                        job_name,
                        frame_range,
                        mode=render_mode,
                        source_file=uploaded_file.name,
                    )

                    # Create job directory
                    job_dir = workspace_service.create_job_directory(
                        job, uploaded_file.getvalue(), uploaded_file.name
                    )

                    # Queue the job
                    render_worker: RenderWorker = st.session_state.render_worker
                    if not render_worker.is_alive:
                        print("Reviving render worker...")
                        st.session_state.render_worker = RenderWorker.get_instance(
                            workspace_service, db_service
                        )
                        st.session_state.render_worker.start()

                    st.session_state.render_worker.enqueue_job(job)

                    st.info("Job submitted")


with cols[1]:
    st.title("📋 Jobs")

    st.markdown(
        """
        <div class="empty-placeholder">
            <h3>Select a Job</h3>
            <p>Click on a job from the list to view its details</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    jobs = db_service.get_all_jobs()

    if jobs:
        df = pd.DataFrame(
            [
                {
                    "Id": job.id,
                    "Job Name": job.name,
                    "Created At": job.created_at,
                    "Source": job.source_file,
                    "Status": "complete"
                    if job.finished_at
                    else (
                        "queued"
                        if job.id != st.session_state.render_worker.current_job
                        else "active"
                    ),
                }
                for job in jobs
            ]
        )
        event = st.dataframe(
            df,
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
            key="queued-jobs",
        )
        if len(event.selection.get("rows")) > 0:
            selected_row = event.selection.get("rows")[0]
            st.session_state.selected_job = df.iloc[selected_row]["Id"]
    else:
        st.markdown(
            """
            <div class="empty-placeholder">
                <p>No Jobs</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

with cols[2]:
    st.title("🔍 Job Detail")
    if "selected_job" not in st.session_state:
        # Show placeholder when no job is selected
        st.markdown(
            """
            <div class="empty-placeholder">
                <h3>Select a Job</h3>
                <p>Click on a job from the list to view its details</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        selected_job_id = st.session_state.selected_job
        job = db_service.get_job(int(selected_job_id))

        print(f"Got {job}")

        job_dir = workspace_service.parse_job_directory(job)
        # Create two columns for job details
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Job ID:**")
            st.markdown("**Job ID:**")
            st.markdown("**Status:**")
            st.markdown("**Render Time:**")
            st.markdown("**Mode:**")
            st.markdown("**Frame Range:**")
            st.markdown("**Source File:**")

        with col2:
            st.markdown(f"`{job.id}`")
            st.markdown(f"`{job.name}`")
            status = "Complete" if job.finished_at else "In Progress"
            st.markdown(f"`{status}`")

            if job.finished_at:
                render_time = job.finished_at - job.created_at
                minutes = int(render_time.total_seconds() // 60)
                seconds = int(render_time.total_seconds() % 60)
                st.markdown(f"`{minutes}m {seconds}s`")
            else:
                st.markdown("`-`")

            st.markdown(f"`{job.mode}`")
            st.markdown(f"`{job.frame_range}`")

            src_file_path = job_dir.absolute() / "src" / str(job.source_file)

            if src_file_path.exists():
                with open(job_dir.absolute() / "src" / job.source_file, "rb") as f:
                    st.download_button(
                        job.source_file,
                        f,
                        job.source_file,
                        mime="application/octet-stream",
                    )
            else:
                st.warning(f'Source {job.source_file} does not exist')

        # Add delete button
        if st.button("🗑️ Delete Job", type="primary", use_container_width=True):
            # Delete job from workspace and database
            if workspace_service.delete_job(job) and db_service.delete_job(job.id):
                st.success("Job deleted successfully")
                # Clear selected job from session state
                del st.session_state.selected_job
                st.rerun()
            else:
                st.error("Failed to delete job")

        # Display render outputs
        st.markdown("### 🎬 Render Outputs")

        output_cols = st.columns(2)

        render_pairs = workspace_service.get_output_files(job)
        # Display compressed JPGs with PNG download links
        for idx, (render_file, static_file) in enumerate(render_pairs):
            with output_cols[idx % 2]:  # Distribute across 3 columns
                if job.mode == RenderMode.still:
                    # Display compressed JPG
                    st.image(
                        str(static_file),
                        caption=render_file.name,  # Show original PNG name
                        use_container_width=True,
                    )
                    # Provide download link for original PNG
                    if render_file.exists():
                        with open(render_file, "rb") as f:
                            st.download_button(
                                f"Download {render_file.name}",
                                f,
                                file_name=render_file.name,
                                mime="image/png",
                            )
                else:
                    st.video(
                        str(static_file),
                    )
                    if static_file.exists():
                        # Add download button for the video
                        with open(static_file, "rb") as f:
                            st.download_button(
                                f"Download {static_file.name}",
                                f,
                                file_name=static_file.name,
                                mime="video/mp4",
                            )
