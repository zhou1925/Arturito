import os
import logging
from typing import Optional, Dict, Union
import cloudinary
import cloudinary.uploader
import io

logger = logging.getLogger(__name__)

class CloudinaryService:
    """
    Handles interactions with Cloudinary API for uploading and deleting files.
    Files are uploaded to custom folders based on file type.
    """

    def __init__(self, cloud_name: str, api_key: str, api_secret: str, secure: bool = True):
        if not cloud_name or not api_key or not api_secret:
            logger.error("Cloudinary credentials are missing")
            raise ValueError("Cloudinary credentials are required")
        try:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=secure
            )
            logger.info("CloudinaryService successfully configured")
        except Exception as e:
            logger.error(f"Failed to configure Cloudinary: {e}", exc_info=True)
            raise ConnectionError(f"Could not configure Cloudinary: {e}") from e

    def _determine_folder_and_resource_type(self, file_name: str) -> (str, str):
        """
        Determines the destination folder and resource type based on the file extension.
        """
        ext = os.path.splitext(file_name)[1].lower().strip('.')
        # Defaults
        folder = "others"
        resource_type = "raw"

        if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg']:
            folder = "images"
            resource_type = "image"
        elif ext in ['mp4', 'mov', 'avi', 'mkv']:
            folder = "videos"
            resource_type = "video"
        elif ext in ['mp3', 'wav', 'ogg']:
            folder = "audio"
            # Cloudinary treats audio as a type of video.
            resource_type = "video"
        elif ext in ['pdf', 'txt', 'md']:
            folder = "documents"
            resource_type = "raw"
        return folder, resource_type

    def upload_file(self, file_data: Union[str, io.BytesIO], public_id: Optional[str] = None, file_name: Optional[str] = None) -> Optional[Dict]:
        """
        Uploads a file to Cloudinary into a folder determined by its file type.
        
        Args:
            file_data: Either a local file path / URL or a file-like object (e.g., io.BytesIO).
            public_id: An optional public ID to assign.
            file_name: Required if file_data is a file-like object. It should include the extension.
        
        Returns:
            A dictionary with the upload result or None if an error occurred.
        """
        # Determine if file_data is a path/URL or a file-like object
        if isinstance(file_data, str):
            # If it's a string, assume it's a path or URL.
            if not os.path.exists(file_data) and not file_data.startswith("http"):
                logger.error(f"File not found: {file_data}")
                raise FileNotFoundError(f"File not found: {file_data}")
            # Use file_data as the file name if file_name isn't provided
            if not file_name:
                file_name = os.path.basename(file_data)
        elif isinstance(file_data, io.BytesIO):
            if not file_name:
                logger.error("file_name must be provided when uploading a file-like object")
                raise ValueError("file_name is required for in-memory file uploads")
        else:
            logger.error("file_data must be either a file path/URL or a file-like object")
            raise ValueError("Invalid type for file_data")

        folder, resource_type = self._determine_folder_and_resource_type(file_name)
        try:
            logger.debug(f"Uploading file: {file_name} to folder: {folder} with resource_type: {resource_type}")
            upload_result = cloudinary.uploader.upload(
                file_data,
                folder=folder,
                public_id=public_id,
                resource_type=resource_type
            )
            logger.info(f"File uploaded successfully. Public ID: {upload_result.get('public_id')}")
            return upload_result
        except Exception as e:
            logger.error(f"Error uploading file {file_name}: {e}", exc_info=True)
            return None

    def destroy_file(self, public_id: str, file_name: Optional[str] = None) -> Optional[Dict]:
        """
        Deletes a file on Cloudinary using its public ID.
        
        If file_name is provided, the resource type is determined based on its extension;
        otherwise, defaults to 'raw'.
        """
        resource_type = "raw"
        if file_name:
            _, resource_type = self._determine_folder_and_resource_type(file_name)
        try:
            logger.debug(f"Destroying file with Public ID: {public_id} and resource_type: {resource_type}")
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            logger.info(f"File with Public ID {public_id} destroyed successfully: {result}")
            return result
        except Exception as e:
            logger.error(f"Error destroying file with Public ID {public_id}: {e}", exc_info=True)
            return None

if __name__ == "__main__":
    import io
    import logging
    import time
    import sys
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    try:
        from config import ConfigManager
    except ImportError:
        print("Error: Could not import ConfigManager. Make sure 'config.py' exists in the parent directory.")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    config = ConfigManager()
    CLOUDINARY_CLOUD_NAME = config.get_setting("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = config.get_setting("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = config.get_setting("CLOUDINARY_API_SECRET")

    try:
        cloudinary_service = CloudinaryService(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET
        )

        # --- Testing File Upload using a URL ---
        test_file_url = "https://res.cloudinary.com/demo/image/upload/getting-started/shoes.jpg"
        upload_result_url = cloudinary_service.upload_file(test_file_url)
        if upload_result_url:
            print("URL Upload Test Successful")
            print(f"Secure URL: {upload_result_url.get('secure_url')}")
            public_id_url = upload_result_url.get('public_id')
        else:
            print("URL Upload Test Failed")

        # --- Testing File Upload using an in-memory buffer ---
        # Create an in-memory text file
        text_content = "Hello, Cloudinary!"
        buffer = io.BytesIO(text_content.encode('utf-8'))
        # Provide a file name so that the extension can be used for folder/resource_type determination.
        file_name = "example.txt"

        upload_result_buffer = cloudinary_service.upload_file(buffer, file_name=file_name)
        if upload_result_buffer:
            print("Buffer Upload Test Successful")
            print(f"Secure URL: {upload_result_buffer.get('secure_url')}")
            public_id_buffer = upload_result_buffer.get('public_id')
        else:
            print("Buffer Upload Test Failed")

        time.sleep(60)
        # --- Testing File Destruction ---
        if public_id_buffer:
            destroy_result = cloudinary_service.destroy_file(public_id_buffer, file_name=file_name)
            if destroy_result and destroy_result.get("result") == "ok":
                print("Destroy Test Successful")
            else:
                print("Destroy Test Failed")
        else:
            print("No public_id available for destruction test.")
    except Exception as e:
        logger.exception("An error occurred during testing.")
