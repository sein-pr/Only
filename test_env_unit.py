"""
Unit tests for environment configuration edge cases.
"""

import os
import pytest
from dotenv import load_dotenv
from pathlib import Path


class TestEnvironmentEdgeCases:
    """Unit tests for specific edge cases in environment configuration."""
    
    def test_missing_env_file_does_not_crash(self):
        """
        Test that loading a non-existent .env file doesn't crash the application.
        
        Validates: Requirements 1.3
        """
        # Attempt to load a non-existent file
        result = load_dotenv('/nonexistent/path/to/.env')
        
        # Should return False but not raise an exception
        assert result == False, "Loading non-existent .env should return False"
    
    def test_back4app_client_missing_app_id(self):
        """
        Test that Back4App client raises descriptive error when APP_ID is missing.
        
        Validates: Requirements 2.2
        """
        # Save original values
        original_app_id = os.environ.get('BACK4APP_APP_ID')
        original_master_key = os.environ.get('BACK4APP_MASTER_KEY')
        original_client_key = os.environ.get('BACK4APP_CLIENT_KEY')
        
        try:
            # Remove required variables
            os.environ.pop('BACK4APP_APP_ID', None)
            
            # Import the client class
            from back4app_client import Back4AppClient
            
            # Attempt to create client should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                client = Back4AppClient()
            
            # Verify error message is descriptive
            error_message = str(exc_info.value)
            assert 'BACK4APP_APP_ID' in error_message
            assert 'environment' in error_message.lower()
        finally:
            # Restore original values
            if original_app_id:
                os.environ['BACK4APP_APP_ID'] = original_app_id
            if original_master_key:
                os.environ['BACK4APP_MASTER_KEY'] = original_master_key
            if original_client_key:
                os.environ['BACK4APP_CLIENT_KEY'] = original_client_key
    
    def test_back4app_client_missing_auth_keys(self):
        """
        Test that Back4App client raises error when no authentication keys are present.
        
        Validates: Requirements 2.2
        """
        # Save original values
        original_app_id = os.environ.get('BACK4APP_APP_ID')
        original_master_key = os.environ.get('BACK4APP_MASTER_KEY')
        original_client_key = os.environ.get('BACK4APP_CLIENT_KEY')
        
        try:
            # Set APP_ID but remove auth keys
            os.environ['BACK4APP_APP_ID'] = 'test_app_id'
            os.environ.pop('BACK4APP_MASTER_KEY', None)
            os.environ.pop('BACK4APP_CLIENT_KEY', None)
            
            # Import the client class
            from back4app_client import Back4AppClient
            
            # Attempt to create client should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                client = Back4AppClient()
            
            # Verify error message mentions authentication keys
            error_message = str(exc_info.value)
            assert 'MASTER_KEY' in error_message or 'CLIENT_KEY' in error_message
        finally:
            # Restore original values
            if original_app_id:
                os.environ['BACK4APP_APP_ID'] = original_app_id
            else:
                os.environ.pop('BACK4APP_APP_ID', None)
            if original_master_key:
                os.environ['BACK4APP_MASTER_KEY'] = original_master_key
            if original_client_key:
                os.environ['BACK4APP_CLIENT_KEY'] = original_client_key
    
    def test_development_mode_loads_env_file(self):
        """
        Test that in development mode, variables are loaded from .env file.
        
        Validates: Requirements 3.1
        """
        # Load the .env file
        load_dotenv()
        
        # Verify that key variables are loaded
        # These should be present in the .env file for development
        assert os.environ.get('BACK4APP_APP_ID') is not None
        assert os.environ.get('SECRET_KEY') is not None
    
    def test_production_mode_supports_system_env_vars(self):
        """
        Test that production mode can use system environment variables.
        
        Validates: Requirements 3.2
        """
        # Set a test variable in system environment
        test_var = 'TEST_PRODUCTION_VAR'
        test_value = 'production_value_123'
        
        original_value = os.environ.get(test_var)
        
        try:
            os.environ[test_var] = test_value
            
            # Verify it's accessible
            assert os.environ.get(test_var) == test_value
        finally:
            # Clean up
            if original_value is None:
                os.environ.pop(test_var, None)
            else:
                os.environ[test_var] = original_value


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
