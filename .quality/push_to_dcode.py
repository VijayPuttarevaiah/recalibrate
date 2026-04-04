#!/usr/bin/env python3

"""
Python script to upload project inputs to DCodeHub.
Replaces the bash script to avoid shell environment issues in CI.
"""

import sys
import os
import requests


def main():
    # --- ARGUMENT VALIDATION ---
    if len(sys.argv) != 5:
        print("Error: Incorrect number of arguments.", file=sys.stderr)
        print(
            f"Usage: {sys.argv[0]} <project-id> <api-key> <directory-to-upload> <commit-hash>",
            file=sys.stderr,
        )
        sys.exit(1)

    project_id = sys.argv[1]
    api_key = sys.argv[2]
    file_dir = sys.argv[3]
    commit_sha = sys.argv[4]

    # Check if the provided directory exists
    if not os.path.isdir(file_dir):
        print(f"Error: Directory '{file_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    # --- POPULATE FILE ARGUMENTS ---
    print(f"Collecting files from '{file_dir}'...")
    files_to_upload = {}
    open_files = []  # To store file handles for proper closing

    try:
        # Find all files in the directory
        file_paths = []
        for entry in os.listdir(file_dir):
            full_path = os.path.join(file_dir, entry)
            if os.path.isfile(full_path):
                file_paths.append(full_path)

        # Check if any files were actually found
        if not file_paths:
            print(f"No files found in '{file_dir}'. Nothing to upload.")
            sys.exit(0)

        # Prepare files for multipart upload
        for i, file_path in enumerate(file_paths, 1):
            field_name = f"file{i}"
            # Open file in binary read mode
            file_handle = open(file_path, "rb")
            open_files.append(file_handle)
            # Add to the files dictionary
            files_to_upload[field_name] = (os.path.basename(file_path), file_handle)

        # --- PREPARE REQUEST ---
        url = f"https://dcodehub.com/api/projects/{project_id}/upload/"
        headers = {
            "X-API-Key": api_key,
            "X-Commit-ID": commit_sha,
            "X-Tool": "DesigniteJava",
        }

        print(f"Sending {len(files_to_upload)} file(s) to {url}...")

        # --- EXECUTE REQUEST ---
        response = requests.post(url, headers=headers, files=files_to_upload)

        # Check for HTTP errors (e.g., 404, 500)
        # This is equivalent to curl's '-f' flag
        response.raise_for_status()

        # --- OUTPUT RESULTS ---
        print("Upload successful.")
        print(f"Server response: {response.text}")
        sys.exit(0)

    except requests.exceptions.HTTPError as e:
        # This catches 4xx and 5xx responses
        print(
            f"Error: HTTP request failed with status code {e.response.status_code}.",
            file=sys.stderr,
        )
        print(f"Server response (if any): {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        # This catches other errors (connection, timeout, etc.)
        print(f"Error: Request failed. Details: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Ensure all file handles are closed
        for f in open_files:
            f.close()


if __name__ == "__main__":
    main()
