import os
from dotenv import load_dotenv
from datetime import datetime
from redminelib import Redmine
import requests

# Load environment variables
load_dotenv()

REDMINE_URL = os.getenv('REDMINE_URL')
REDMINE_API_KEY = os.getenv('REDMINE_API_KEY')
TIMECAMP_API_TOKEN = os.getenv('TIMECAMP_API_TOKEN2')
TIMECAMP_TASK_ID = os.getenv('TIMECAMP_TASK_ID')

def get_redmine_projects():
    redmine = Redmine(REDMINE_URL, key=REDMINE_API_KEY)
    all_projects = redmine.project.all()
    active_projects = [project for project in all_projects if project.status == 1]  # Assuming status 1 means active
    return active_projects

def get_timecamp_projects():
    url = "https://app.timecamp.com/third_party/api/tasks"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {TIMECAMP_API_TOKEN}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    # Check if the response is a dictionary
    if isinstance(data, dict):
        # Extract the projects from the dictionary
        return list(data.values())
    elif isinstance(data, list):
        # If it's already a list, return it as is
        return data
    else:
        print(f"Unexpected response format: {type(data)}")
        return []

def create_timecamp_project(name, project_id):
    url = "https://app.timecamp.com/third_party/api/tasks"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {TIMECAMP_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'name': name,
        'parent_id': TIMECAMP_TASK_ID,
        'external_task_id': f'redmine_{project_id}'
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def archive_timecamp_project(task_id):
    url = f"https://app.timecamp.com/third_party/api/tasks"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {TIMECAMP_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'archived': 1,
        'task_id': task_id
    }
    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def sync_projects():
    redmine_projects = get_redmine_projects()
    timecamp_projects = get_timecamp_projects()

    timecamp_project_ids = {project.get('external_task_id'): project for project in timecamp_projects}
    active_redmine_project_ids = {f'redmine_{project.id}' for project in redmine_projects}

    for redmine_project in redmine_projects:
        external_task_id = f'redmine_{redmine_project.id}'
        if external_task_id not in timecamp_project_ids:
            print(f"Creating new TimeCamp project: {redmine_project.name}")
            create_timecamp_project(redmine_project.name, redmine_project.id)
        else:
            print(f"Project already exists in TimeCamp: {redmine_project.name}")

    for timecamp_project in timecamp_projects:
        external_task_id = timecamp_project.get('external_task_id')
        if external_task_id and isinstance(external_task_id, str) and external_task_id.startswith('redmine_'):
            if external_task_id not in active_redmine_project_ids and not timecamp_project.get('archived'):
                print(f"Archiving TimeCamp project: {timecamp_project['name']}")
                archive_timecamp_project(timecamp_project['task_id'])

    print("Synchronization complete.")

if __name__ == "__main__":
    print(f"Starting synchronization at {datetime.now()}")
    sync_projects()
    print(f"Synchronization finished at {datetime.now()}")