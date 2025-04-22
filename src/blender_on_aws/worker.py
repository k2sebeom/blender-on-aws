import streamlit as st
import pandas as pd

from blender_on_aws.models.job import RenderMode
from blender_on_aws.workers.render_worker import RenderWorker
from blender_on_aws.utils.styles import get_common_styles
from blender_on_aws.utils.config_init import initialize_app
import streamlit as st
import pandas as pd


def main():
    # Initialize app and get config/workspace service
    _, workspace_service, db_service = initialize_app()
    render_worker = RenderWorker(workspace_service, db_service)

    render_worker.run()
