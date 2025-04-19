import streamlit as st
import pandas as pd
from pathlib import Path
from src.utils.config_init import initialize_app
from src.utils.styles import get_common_styles

# Set page config
st.set_page_config(
    page_title="Job History - Blender Online Renderer", page_icon="📋", layout="wide"
)

# Initialize app and get config/workspace service
config, workspace_service = initialize_app()

# Add custom CSS
st.markdown(get_common_styles(), unsafe_allow_html=True)


def main():
    st.title("📋 Job History")

    # Create two columns for the layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Jobs")

        # Initialize page number in session state if not exists
        if "page" not in st.session_state:
            st.session_state.page = 1

        # Get paginated jobs
        jobs, total_pages = workspace_service.get_paginated_jobs(st.session_state.page)

        if jobs:
            # Create DataFrame and display table
            df = pd.DataFrame(
                [
                    {
                        "Job Name": job["name"],
                        "Created At": job["created_at"],
                        "Number of Runs": job["num_runs"],
                    }
                    for job in jobs
                ]
            )
            event = st.dataframe(
                df,
                on_select="rerun",
                selection_mode="single-row",
                hide_index=True,
            )
            if len(event.selection.get("rows")) > 0:
                selected_row = event.selection.get("rows")[0]
                st.session_state.selected_job = df.iloc[selected_row]["Job Name"]

            # Pagination controls
            cols = st.columns(4)
            with cols[0]:
                if st.button("⏪ First", disabled=st.session_state.page == 1):
                    st.session_state.page = 1
                    st.rerun()
            with cols[1]:
                if st.button("◀️", disabled=st.session_state.page == 1):
                    st.session_state.page -= 1
                    st.rerun()
            with cols[2]:
                st.write(f"Page {st.session_state.page} of {total_pages}")
            with cols[3]:
                if st.button("▶️", disabled=st.session_state.page == total_pages):
                    st.session_state.page += 1
                    st.rerun()
        else:
            st.info("No jobs found. Upload a .blend file to start rendering!")

    with col2:
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
            st.subheader(f"Job Details: {st.session_state.selected_job}")

            # Add delete button
            if st.button(
                "🗑️ Delete Job",
                type="secondary",
                use_container_width=True,
            ):
                if workspace_service.delete_job(st.session_state.selected_job):
                    del st.session_state.selected_job
                    st.rerun()
                else:
                    st.error("Failed to delete job")

            # Get runs for the selected job
            runs = workspace_service.get_job_runs(st.session_state.selected_job)

            if runs:
                # Create a dropdown to select run
                selected_run = st.selectbox(
                    "Select Run",
                    runs,
                    index=0,  # Select most recent run by default
                    format_func=lambda x: f"Run {x}",
                )

                if selected_run:
                    # Get run statistics
                    stats = workspace_service.get_run_stats(
                        st.session_state.selected_job, selected_run
                    )

                    # Display run statistics
                    st.markdown("### Run Statistics")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Rendered Files", stats["num_files"])
                    with col2:
                        # Convert seconds to minutes and seconds
                        total_seconds = int(stats["render_time"])
                        minutes = total_seconds // 60
                        seconds = total_seconds % 60
                        st.metric("Total Render Time", f"{minutes} min {seconds} sec")

                    # Get and display run details
                    source_files, render_files = workspace_service.get_run_details(
                        st.session_state.selected_job, selected_run
                    )

                    # Display source files
                    if source_files:
                        st.markdown("### Source Files")
                        for src_file in source_files:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.text(src_file.name)
                            with col2:
                                with open(src_file, "rb") as f:
                                    st.download_button(
                                        "Download",
                                        f,
                                        file_name=src_file.name,
                                        mime="application/octet-stream",
                                    )

                    # Display render outputs
                    st.markdown("### Render Outputs")
                    if render_files:
                        # Check if this is an animation or still image based on mode
                        is_animation = stats.get("mode") == "Animation"
                        
                        if is_animation:
                            cols = st.columns(2)
                            # For animation, just get mp4 file
                            mp4_file = render_files[0][1]
                            with cols[0]:
                                st.video(str(mp4_file))
                                # Add download button for the video
                                with open(mp4_file, "rb") as f:
                                    st.download_button(
                                        label="Download Animation",
                                        data=f,
                                        file_name=mp4_file.name,
                                        mime="video/mp4",
                                    )
                        else:  # Still image outputs
                            # Create 3 columns for the grid
                            cols = st.columns(3)

                            # Display compressed JPGs with PNG download links
                            for idx, (jpg_file, png_file) in enumerate(render_files):
                                with cols[idx % 3]:  # Distribute across 3 columns
                                    # Display compressed JPG
                                    st.image(
                                        jpg_file,
                                        caption=png_file.name,  # Show original PNG name
                                        use_container_width=True,
                                    )
                                    # Provide download link for original PNG
                                    with open(png_file, "rb") as f:
                                        png_bytes = f.read()
                                        st.download_button(
                                            f"Download {png_file.name}",
                                            png_bytes,
                                            file_name=png_file.name,
                                            mime="image/png",
                                        )
            else:
                st.info("No runs found for this job.")


if __name__ == "__main__":
    main()
