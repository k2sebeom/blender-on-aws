import streamlit as st
import pandas as pd
from src.config.config_loader import ConfigLoader
from src.services.workspace_service import WorkspaceService
import argparse

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
st.set_page_config(page_title="Job History - Blender Online Renderer", page_icon="📋", layout="wide")

# Add custom CSS
st.markdown(
    """
    <style>
    .main {
        padding: 2rem;
    }
    .job-table {
        margin-bottom: 1rem;
    }
    .empty-placeholder {
        text-align: center;
        padding: 2rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def main():
    st.title("📋 Job History")
    
    # Create two columns for the layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Jobs")
        
        # Initialize page number in session state if not exists
        if 'page' not in st.session_state:
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
                        "Number of Runs": job["num_runs"]
                    }
                    for job in jobs
                ]
            )
            event = st.dataframe(
                df,
                on_select='rerun',
                selection_mode='single-row',
                hide_index=True,
            )
            if len(event.selection.get('rows')) > 0:
                selected_row = event.selection.get('rows')[0]
                st.session_state.selected_job = df.iloc[selected_row]['Job Name']

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
        if 'selected_job' not in st.session_state:
            # Show placeholder when no job is selected
            st.markdown(
                """
                <div class="empty-placeholder">
                    <h3>Select a Job</h3>
                    <p>Click on a job from the list to view its details</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.subheader(f"Job Details: {st.session_state.selected_job}")
            
            # Get runs for the selected job
            runs = workspace_service.get_job_runs(st.session_state.selected_job)
            
            if runs:
                # Create a dropdown to select run
                selected_run = st.selectbox(
                    "Select Run",
                    runs,
                    index=0,  # Select most recent run by default
                    format_func=lambda x: f"Run {x}"
                )
                
                if selected_run:
                    # Get run statistics
                    stats = workspace_service.get_run_stats(
                        st.session_state.selected_job,
                        selected_run
                    )
                    
                    # Display run statistics
                    st.markdown("### Run Statistics")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Rendered Files", stats["num_files"])
                    with col2:
                        st.metric("Total Render Time", f"{stats['render_time']} min")
                    
                    # Get and display run details
                    source_files, render_files = workspace_service.get_run_details(
                        st.session_state.selected_job,
                        selected_run
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
                                        mime="application/octet-stream"
                                    )
                    
                    # Display render outputs
                    if render_files:
                        st.markdown("### Render Outputs")
                        for render_file in render_files:
                            with open(render_file, "rb") as f:
                                image_bytes = f.read()
                                st.image(image_bytes, caption=render_file.name, use_container_width=True)
                                st.download_button(
                                    f"Download {render_file.name}",
                                    image_bytes,
                                    file_name=render_file.name,
                                    mime="image/png"
                                )
            else:
                st.info("No runs found for this job.")

if __name__ == "__main__":
    main()
