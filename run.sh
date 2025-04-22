#!/bin/bash
streamlit run src/blender_on_aws/controller.py \
    --server.address 0.0.0.0 \
    --server.maxUploadSize 1000000 \
    -- -c config.yaml
