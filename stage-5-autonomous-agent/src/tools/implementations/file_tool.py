"""File operations tool implementation.

This tool provides file system operations.
"""

import os
import json
from typing import Dict, Any
from tools.base_tool import BaseTool, ToolResult, ToolParameter


class ReadFileTool(BaseTool):
    """Tool for reading files."""

    name = "read_file"
    description = "Read the contents of a file"
    category = "file"
    parameters = [
        ToolParameter(
            name="file_path",
            type="string",
            description="Path to the file to read",
            required=True
        ),
        ToolParameter(
            name="encoding",
            type="string",
            description="File encoding (default: utf-8)",
            required=False
        )
    ]

    def execute(self, **kwargs) -> ToolResult:
        """Execute file read.

        Args:
            file_path: Path to file
            encoding: File encoding

        Returns:
            File contents
        """
        file_path = kwargs.get('file_path')
        encoding = kwargs.get('encoding', 'utf-8')

        if not file_path:
            return ToolResult(
                success=False,
                error="file_path parameter is required"
            )

        # Security check - prevent directory traversal
        if '..' in file_path or file_path.startswith('/'):
            return ToolResult(
                success=False,
                error="Invalid file path (directory traversal not allowed)"
            )

        try:
            # In Lambda, files would be in /tmp or mounted filesystem
            full_path = os.path.join('/tmp', file_path)

            if not os.path.exists(full_path):
                return ToolResult(
                    success=False,
                    error=f"File not found: {file_path}"
                )

            with open(full_path, 'r', encoding=encoding) as f:
                content = f.read()

            return ToolResult(
                success=True,
                data={
                    "file_path": file_path,
                    "content": content,
                    "size": len(content)
                },
                metadata={
                    "encoding": encoding
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to read file: {str(e)}"
            )


class WriteFileTool(BaseTool):
    """Tool for writing files."""

    name = "write_file"
    description = "Write content to a file"
    category = "file"
    parameters = [
        ToolParameter(
            name="file_path",
            type="string",
            description="Path to the file to write",
            required=True
        ),
        ToolParameter(
            name="content",
            type="string",
            description="Content to write to the file",
            required=True
        ),
        ToolParameter(
            name="mode",
            type="string",
            description="Write mode - 'overwrite' or 'append' (default: overwrite)",
            required=False
        )
    ]

    def execute(self, **kwargs) -> ToolResult:
        """Execute file write.

        Args:
            file_path: Path to file
            content: Content to write
            mode: Write mode

        Returns:
            Write result
        """
        file_path = kwargs.get('file_path')
        content = kwargs.get('content')
        mode = kwargs.get('mode', 'overwrite')

        if not file_path or content is None:
            return ToolResult(
                success=False,
                error="file_path and content parameters are required"
            )

        # Security check
        if '..' in file_path or file_path.startswith('/'):
            return ToolResult(
                success=False,
                error="Invalid file path (directory traversal not allowed)"
            )

        try:
            # In Lambda, write to /tmp
            full_path = os.path.join('/tmp', file_path)

            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            write_mode = 'w' if mode == 'overwrite' else 'a'

            with open(full_path, write_mode, encoding='utf-8') as f:
                f.write(content)

            return ToolResult(
                success=True,
                data={
                    "file_path": file_path,
                    "bytes_written": len(content),
                    "mode": mode
                },
                metadata={
                    "full_path": full_path
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to write file: {str(e)}"
            )


class ListFilesTool(BaseTool):
    """Tool for listing files in a directory."""

    name = "list_files"
    description = "List files in a directory"
    category = "file"
    parameters = [
        ToolParameter(
            name="directory",
            type="string",
            description="Directory path to list (default: /tmp)",
            required=False
        ),
        ToolParameter(
            name="pattern",
            type="string",
            description="Filter files by pattern (e.g., '*.txt')",
            required=False
        )
    ]

    def execute(self, **kwargs) -> ToolResult:
        """Execute directory listing.

        Args:
            directory: Directory path
            pattern: File pattern filter

        Returns:
            List of files
        """
        directory = kwargs.get('directory', '/tmp')
        pattern = kwargs.get('pattern', '*')

        try:
            # Security check
            if '..' in directory:
                return ToolResult(
                    success=False,
                    error="Invalid directory path"
                )

            full_path = os.path.join('/tmp', directory) if not directory.startswith('/') else directory

            if not os.path.exists(full_path):
                return ToolResult(
                    success=False,
                    error=f"Directory not found: {directory}"
                )

            files = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                is_file = os.path.isfile(item_path)

                # Apply pattern filter
                if pattern != '*':
                    import fnmatch
                    if not fnmatch.fnmatch(item, pattern):
                        continue

                files.append({
                    "name": item,
                    "type": "file" if is_file else "directory",
                    "size": os.path.getsize(item_path) if is_file else 0
                })

            return ToolResult(
                success=True,
                data={
                    "directory": directory,
                    "files": files,
                    "count": len(files)
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to list directory: {str(e)}"
            )


class ParseJSONTool(BaseTool):
    """Tool for parsing JSON data."""

    name = "parse_json"
    description = "Parse and validate JSON data"
    category = "file"
    parameters = [
        ToolParameter(
            name="json_string",
            type="string",
            description="JSON string to parse",
            required=True
        )
    ]

    def execute(self, **kwargs) -> ToolResult:
        """Execute JSON parsing.

        Args:
            json_string: JSON string

        Returns:
            Parsed JSON
        """
        json_string = kwargs.get('json_string')

        if not json_string:
            return ToolResult(
                success=False,
                error="json_string parameter is required"
            )

        try:
            data = json.loads(json_string)

            return ToolResult(
                success=True,
                data={
                    "parsed": data,
                    "type": type(data).__name__
                },
                metadata={
                    "original_length": len(json_string)
                }
            )

        except json.JSONDecodeError as e:
            return ToolResult(
                success=False,
                error=f"Invalid JSON: {str(e)}"
            )
