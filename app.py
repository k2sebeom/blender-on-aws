import streamlit as st

# Create navigation
pg = st.navigation(
    [
        st.Page("home.py", title="Render", icon="🎨"),
        st.Page("job_history.py", title="Job History", icon="📋"),
    ]
)

# Run the selected page
pg.run()
