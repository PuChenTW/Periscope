#!/bin/bash
# .claude/hooks/format-python.sh
# This claude code hook formats Python files using ruff via uvx.

input_json=$(cat)

file_path=$(echo "$input_json" | jq -r '.tool_input.file_path // empty')

# Change this to your project's root directory if needed
project_path="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Exit silently if no file path - hook may be called for non-file operations
if [[ -z "$file_path" ]]; then
    exit 0
fi

if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed. Please install it first." >&2
    exit 1
fi

if ! command -v uvx &> /dev/null; then
    echo "Error: uvx is not installed. Please install uv first: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi

if [[ "$file_path" =~ \.py$ ]]; then
    echo "Formatting Python file: $file_path"
    # Ignore unused imports (F401) since claude code tend to add the imports before implementing details.
    # Don't exit on error - let Claude see the error output to fix the code
    if ! (cd "$project_path" && uvx ruff format "$file_path" && uvx ruff check --ignore F401 --fix "$file_path"); then
        echo "Warning: Formatting had issues for $file_path - check output above" >&2
    fi
fi
