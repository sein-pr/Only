"""
ImgBB Image Upload Helper

Uploads images to ImgBB and returns the hosted URL.
This ensures images are accessible from anywhere (not just local filesystem).
"""
import os
import base64
import requests
from werkzeug.datastructures import FileStorage


class ImgBBUploader:
    """Helper class for uploading images to ImgBB"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('IMGBB_API_KEY')
        self.upload_url = 'https://api.imgbb.com/1/upload'
        
        if not self.api_key:
            raise ValueError("ImgBB API key not found. Set IMGBB_API_KEY environment variable.")
    
    def upload_file(self, file_storage, name=None):
        """
        Upload a file to ImgBB
        
        Args:
            file_storage: FileStorage object from Flask request.files
            name: Optional custom name for the file
            
        Returns:
            dict: Response from ImgBB API containing image URLs
            
        Raises:
            Exception: If upload fails
        """
        if not isinstance(file_storage, FileStorage):
            raise ValueError("file_storage must be a FileStorage object")
        
        # Read file and convert to base64
        file_data = file_storage.read()
        base64_image = base64.b64encode(file_data).decode('utf-8')
        
        # Reset file pointer in case it's needed again
        file_storage.seek(0)
        
        # Prepare request
        payload = {
            'key': self.api_key,
            'image': base64_image
        }
        
        if name:
            payload['name'] = name
        
        # Upload to ImgBB
        response = requests.post(self.upload_url, data=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if not result.get('success'):
            raise Exception(f"ImgBB upload failed: {result}")
        
        return result['data']
    
    def upload_multiple(self, file_storages, names=None):
        """
        Upload multiple files to ImgBB
        
        Args:
            file_storages: List of FileStorage objects
            names: Optional list of custom names
            
        Returns:
            list: List of image data dicts from ImgBB
        """
        results = []
        names = names or [None] * len(file_storages)
        
        for file_storage, name in zip(file_storages, names):
            try:
                result = self.upload_file(file_storage, name)
                results.append(result)
            except Exception as e:
                print(f"Failed to upload {name or 'image'}: {e}")
                # Continue with other uploads
        
        return results
    
    def get_display_url(self, upload_result):
        """Extract the display URL from upload result"""
        return upload_result.get('display_url') or upload_result.get('url')
    
    def get_thumbnail_url(self, upload_result):
        """Extract the thumbnail URL from upload result"""
        if 'thumb' in upload_result:
            return upload_result['thumb'].get('url')
        return self.get_display_url(upload_result)


# Convenience function for quick uploads
def upload_image_to_imgbb(file_storage, name=None):
    """
    Quick function to upload an image to ImgBB
    
    Args:
        file_storage: FileStorage object from Flask
        name: Optional custom name
        
    Returns:
        str: The display URL of the uploaded image
    """
    uploader = ImgBBUploader()
    result = uploader.upload_file(file_storage, name)
    return uploader.get_display_url(result)
