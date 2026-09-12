#!/usr/bin/env bash
# exit on error
set -o errexit

echo '=== 1. Building React Frontend ==='
cd frontend
npm install
npm run build
cd ..

echo '=== 2. Installing Python Dependencies ==='
pip install -r backend/requirements.txt

echo '=== 3. Running Database Migrations ==='
python backend/manage.py migrate

echo '=== 4. Ingesting CSV Datasets ==='
python backend/manage.py import_data

echo '=== 5. Collecting Static Files ==='
python backend/manage.py collectstatic --no-input

echo '=== Build Complete ==='
