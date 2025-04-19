#!/bin/bash
streamlit run app.py \
    --server.address 0.0.0.0 \
    --server.maxUploadSize 1000000 \
    -- -c config.yaml
