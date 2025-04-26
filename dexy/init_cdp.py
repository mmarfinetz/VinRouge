import os
import json
from pathlib import Path

def init_cdp_key():
    """Initialize CDP API key file from environment variable."""
    
    # Get CDP API key from environment variable
    cdp_key_json_content = os.environ.get('CDP_API_KEY_JSON')
    if not cdp_key_json_content:
        raise ValueError("CDP_API_KEY_JSON environment variable not set")

    try:
        # Parse the JSON content
        cdp_key_data = json.loads(cdp_key_json_content)
        
        # Create the Downloads directory in root if it doesn't exist
        downloads_path = Path('/root/Downloads')
        downloads_path.mkdir(parents=True, exist_ok=True)
        
        # Write the CDP API key file
        key_file_path = downloads_path / 'cdp_api_key.json'
        with open(key_file_path, 'w') as f:
            json.dump(cdp_key_data, f, indent=2)
            
        # Set proper permissions
        os.chmod(key_file_path, 0o600)
        
        print(f"CDP API key file created successfully at {key_file_path}")
        return True
        
    except json.JSONDecodeError:
        print("Error: Failed to parse CDP_API_KEY_JSON environment variable")
        return False
    except Exception as e:
        print(f"Error creating CDP API key file: {e}")
        return False

if __name__ == "__main__":
    init_cdp_key() 