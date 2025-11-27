import os
import requests
import json
from urllib.parse import urljoin
from decimal import Decimal

def convert_decimals(obj):
    """Recursively convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    return obj

class Back4AppClient:
    def __init__(self):
        self.app_id = os.environ.get('BACK4APP_APP_ID')
        self.client_key = os.environ.get('BACK4APP_CLIENT_KEY')
        self.master_key = os.environ.get('BACK4APP_MASTER_KEY')
        self.base_url = os.environ.get('BACK4APP_API_URL', 'https://parseapi.back4app.com')
        
        if not self.app_id:
            raise ValueError(
                "Back4App App ID not found in environment variables.\n"
                "Please ensure BACK4APP_APP_ID is set in your .env file or system environment.\n"
                "Example: BACK4APP_APP_ID=your_app_id_here"
            )
            
        self.headers = {
            'X-Parse-Application-Id': self.app_id,
            'Content-Type': 'application/json'
        }
        
        if self.master_key:
            self.headers['X-Parse-Master-Key'] = self.master_key
        elif self.client_key:
            self.headers['X-Parse-REST-API-Key'] = self.client_key
        else:
            raise ValueError(
                "No Back4App authentication keys found in environment variables.\n"
                "Please ensure either BACK4APP_MASTER_KEY or BACK4APP_CLIENT_KEY is set in your .env file.\n"
                "Example: BACK4APP_MASTER_KEY=your_master_key_here\n"
                "     or: BACK4APP_CLIENT_KEY=your_client_key_here"
            )

    def _get_url(self, endpoint):
        return urljoin(self.base_url, endpoint)

    def create(self, class_name, data):
        """Creates a new object in the specified class."""
        url = self._get_url(f'classes/{class_name}')
        # Convert Decimals to floats for JSON serialization
        data = convert_decimals(data)
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def get(self, class_name, object_id):
        """Retrieves a single object by ID."""
        url = self._get_url(f'classes/{class_name}/{object_id}')
        response = requests.get(url, headers=self.headers)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def update(self, class_name, object_id, data):
        """Updates an object."""
        url = self._get_url(f'classes/{class_name}/{object_id}')
        # Convert Decimals to floats for JSON serialization
        data = convert_decimals(data)
        response = requests.put(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def delete(self, class_name, object_id):
        """Deletes an object."""
        url = self._get_url(f'classes/{class_name}/{object_id}')
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def query(self, class_name, where=None, order=None, limit=None, skip=None, include=None, count=None):
        """Queries objects from a class."""
        url = self._get_url(f'classes/{class_name}')
        params = {}
        if where:
            params['where'] = json.dumps(where)
        if order:
            params['order'] = order
        if limit is not None:
            params['limit'] = limit
        if skip is not None:
            params['skip'] = skip
        if include:
            params['include'] = include
        if count is not None:
            params['count'] = count
            
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def login(self, username, password):
        """Logs in a user."""
        url = self._get_url('login')
        params = {'username': username, 'password': password}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def signup(self, user_data):
        """Signs up a new user."""
        url = self._get_url('users')
        # Parse requires 'username' and 'password' in the body
        response = requests.post(url, headers=self.headers, json=user_data)
        response.raise_for_status()
        return response.json()
    
    def request_password_reset(self, email):
        """Requests a password reset."""
        url = self._get_url('requestPasswordReset')
        response = requests.post(url, headers=self.headers, json={'email': email})
        response.raise_for_status()
        return response.json()
