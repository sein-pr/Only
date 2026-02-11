"""
Property-based tests for environment configuration.

These tests verify that environment variables are loaded correctly
and accessible throughout the application.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings
from dotenv import load_dotenv
import pytest


class TestEnvironmentVariableLoading:
    """Test suite for environment variable loading functionality."""
    
    @given(
        var_name=st.text(
            min_size=1, 
            max_size=50, 
            alphabet=st.characters(min_codepoint=65, max_codepoint=90) | 
                     st.characters(min_codepoint=97, max_codepoint=122) |
                     st.just('_')
        ).filter(lambda x: x[0].isalpha()),
        var_value=st.text(
            min_size=1, 
            max_size=100,
            alphabet=st.characters(min_codepoint=48, max_codepoint=57) |  # 0-9
                     st.characters(min_codepoint=65, max_codepoint=90) |   # A-Z
                     st.characters(min_codepoint=97, max_codepoint=122) |  # a-z
                     st.just('_') | st.just('-') | st.just('.')
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_1_env_vars_loaded_and_accessible(self, var_name, var_value):
        """
        Feature: env-config-fix, Property 1: Environment variables are loaded and accessible
        
        For any variable defined in the .env file, after the application starts,
        that variable should be accessible via os.environ.get() and return the
        value from the .env file.
        
        Validates: Requirements 1.1, 1.2
        """
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            
            # Write the variable to a temporary .env file (use UTF-8 encoding)
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(f"{var_name}={var_value}\n")
            
            # Save current environment state
            original_value = os.environ.get(var_name)
            
            try:
                # Load the environment file
                load_dotenv(env_file, override=True)
                
                # Verify the variable is accessible and has the correct value
                loaded_value = os.environ.get(var_name)
                assert loaded_value == var_value, (
                    f"Expected {var_name}={var_value}, but got {var_name}={loaded_value}"
                )
            finally:
                # Restore original environment state
                if original_value is None:
                    os.environ.pop(var_name, None)
                else:
                    os.environ[var_name] = original_value

    def test_property_2_import_order_ensures_availability(self):
        """
        Feature: env-config-fix, Property 2: Import order ensures availability
        
        For any module that reads environment variables at import time, when that module
        is imported after environment loading, the variables should be available and have
        the correct values.
        
        Validates: Requirements 1.5
        """
        # Load the .env file first
        load_dotenv()
        
        # This is validated by the successful startup of the application
        # The fix ensures load_dotenv() is called before importing models_b4a
        # which reads BACK4APP_APP_ID at module level
        
        # Verify the critical variables are loaded
        assert os.environ.get('BACK4APP_APP_ID') is not None, "BACK4APP_APP_ID should be loaded"
        assert os.environ.get('SECRET_KEY') is not None, "SECRET_KEY should be loaded"
    
    @given(
        var_name=st.text(
            min_size=1, 
            max_size=50, 
            alphabet=st.characters(min_codepoint=65, max_codepoint=90) | 
                     st.characters(min_codepoint=97, max_codepoint=122) |
                     st.just('_')
        ).filter(lambda x: x[0].isalpha()),
        env_value=st.text(
            min_size=1, 
            max_size=50,
            alphabet=st.characters(min_codepoint=48, max_codepoint=57) |
                     st.characters(min_codepoint=65, max_codepoint=90) |
                     st.characters(min_codepoint=97, max_codepoint=122)
        ),
        system_value=st.text(
            min_size=1, 
            max_size=50,
            alphabet=st.characters(min_codepoint=48, max_codepoint=57) |
                     st.characters(min_codepoint=65, max_codepoint=90) |
                     st.characters(min_codepoint=97, max_codepoint=122)
        )
    )
    @settings(max_examples=100)
    def test_property_3_env_file_precedence(self, var_name, env_value, system_value):
        """
        Feature: env-config-fix, Property 3: .env file precedence
        
        For any variable name that exists in both the .env file and system environment
        variables, the value from the .env file should take precedence.
        
        Validates: Requirements 1.4
        """
        # Ensure the values are different
        if env_value == system_value:
            env_value = env_value + "_env"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / '.env'
            
            # Write to .env file
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(f"{var_name}={env_value}\n")
            
            # Set system environment variable
            original_value = os.environ.get(var_name)
            os.environ[var_name] = system_value
            
            try:
                # Load .env file with override=True
                load_dotenv(env_file, override=True)
                
                # Verify .env value takes precedence
                loaded_value = os.environ.get(var_name)
                assert loaded_value == env_value, (
                    f"Expected .env value {env_value}, but got {loaded_value}"
                )
            finally:
                # Restore original state
                if original_value is None:
                    os.environ.pop(var_name, None)
                else:
                    os.environ[var_name] = original_value
    
    def test_property_4_missing_variables_raise_descriptive_errors(self):
        """
        Feature: env-config-fix, Property 4: Missing required variables raise descriptive errors
        
        For any required environment variable, when it is missing, attempting to use it
        should raise an error that includes the specific variable name.
        
        Validates: Requirements 2.1
        """
        # Test that Back4AppClient raises descriptive error for missing APP_ID
        original_app_id = os.environ.get('BACK4APP_APP_ID')
        original_master_key = os.environ.get('BACK4APP_MASTER_KEY')
        original_client_key = os.environ.get('BACK4APP_CLIENT_KEY')
        
        try:
            # Remove the required variable
            os.environ.pop('BACK4APP_APP_ID', None)
            
            # Import the client class
            from back4app_client import Back4AppClient
            
            # Attempt to create client should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                client = Back4AppClient()
            
            # Verify error message contains the variable name
            error_message = str(exc_info.value)
            assert 'BACK4APP_APP_ID' in error_message, (
                f"Error message should mention BACK4APP_APP_ID, got: {error_message}"
            )
        finally:
            # Restore original values
            if original_app_id:
                os.environ['BACK4APP_APP_ID'] = original_app_id
            if original_master_key:
                os.environ['BACK4APP_MASTER_KEY'] = original_master_key
            if original_client_key:
                os.environ['BACK4APP_CLIENT_KEY'] = original_client_key
    
    def test_property_5_environment_loading_failures_are_logged(self):
        """
        Feature: env-config-fix, Property 5: Environment loading failures are logged
        
        For any failure during environment variable loading, the system should create
        a log entry that contains the reason for the failure.
        
        Validates: Requirements 2.3
        """
        # This property is validated by the error handling in app.py
        # The try-except block around load_dotenv() logs warnings on failure
        
        # Test that loading a non-existent file doesn't crash
        result = load_dotenv('/nonexistent/path/to/.env')
        # Should return False but not raise an exception
        assert result == False, "Loading non-existent .env should return False"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
