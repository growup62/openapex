import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FilePatcherTool:
    """
    A precision tool that allows the AI to replace specific string blocks 
    within a file without overwriting the entire file contents.
    """
    
    @staticmethod
    def patch_file(filepath: str, old_string: str, new_string: str) -> Dict[str, Any]:
        """Replaces exactly one occurrence of old_string with new_string in the file."""
        if not os.path.exists(filepath):
            return {"error": f"File not found: {filepath}"}
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if old_string not in content:
                # Provide a snippet of the file to help the LLM realize what the actual string is
                snippet = content[:500] + "..." if len(content) > 500 else content
                return {
                    "error": "The target string was not found in the file exactly as provided. Check spacing/indentation.",
                    "file_preview": snippet
                }
                
            # Replace only the first occurrence to avoid unintended mass-edits
            updated_content = content.replace(old_string, new_string, 1)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(updated_content)
                
            return {"status": "success", "message": "File patched successfully."}
            
        except Exception as e:
            logger.error(f"Error patching file {filepath}: {e}")
            return {"error": str(e)}

# The JSON Schema that will be passed to the LLM Router
SYSTEM_PATCH_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "system_patch_file",
        "description": "Precisely replace a specific block of text within a local file. Use this to edit code instead of rewriting the whole file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The absolute or relative path to the file to modify."
                },
                "old_string": {
                    "type": "string",
                    "description": "The exact multi-line string block to be replaced (must match whitespace and indentation perfectly)."
                },
                "new_string": {
                    "type": "string",
                    "description": "The new string block that will replace the old_string."
                }
            },
            "required": ["filepath", "old_string", "new_string"]
        }
    }
}
