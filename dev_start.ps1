# Start Flask backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; python run.py"

# Start React frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm install; npm run dev"