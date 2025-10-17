#!/bin/bash
# Cleanup old documents on Railway database
# Keeps only the latest document for each user

railway run python cleanup_old_documents.py
