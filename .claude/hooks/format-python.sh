#!/bin/bash
# .claude/scripts/format-python.sh
# 自動格式化 Python 檔案的 Hook Script

# 從 stdin 讀取 Claude 傳入的 JSON 資料
input_json=$(cat)

# 使用 jq 提取檔案路徑
file_path=$(echo "$input_json" | jq -r '.tool_input.file_path // empty')

# 檢查是否獲得有效的檔案路徑
if [[ -z "$file_path" ]]; then
    exit 0
fi

# 檢查是否為 Python 檔案
if [[ "$file_path" =~ \.py$ ]]; then
    # 檢查 CLAUDE_PROJECT_DIR 環境變數是否存在
    if [[ -z "$CLAUDE_PROJECT_DIR" ]]; then
        echo "Error: CLAUDE_PROJECT_DIR environment variable not set" >&2
        exit 1
    fi

    # 檢查 backend 目錄是否存在
    if [[ ! -d "$CLAUDE_PROJECT_DIR/backend" ]]; then
        echo "Error: Backend directory not found at $CLAUDE_PROJECT_DIR/backend" >&2
        exit 1
    fi

    # 切換到 backend 目錄並執行格式化指令
    echo "Formatting Python file: $file_path"
    (cd "$CLAUDE_PROJECT_DIR/backend" && make ruff-file FILE="$file_path")

    # 檢查格式化是否成功
    if [[ $? -eq 0 ]]; then
        echo "Successfully formatted: $file_path"
    else
        echo "Warning: Failed to format $file_path" >&2
    fi
fi
