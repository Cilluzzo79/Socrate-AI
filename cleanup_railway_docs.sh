#!/bin/bash
# Cleanup old documents on Railway database
# Keeps only the latest document for each user

railway run python delete_old_documents.py
