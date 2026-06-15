# ============================================================
# ODPlatform Git 上传脚本
# ============================================================

# 使用方法：
# 1. 打开 Git Bash 或 PowerShell
# 2. 运行：cd d:\od\ODPlatform
# 3. 运行：powershell -ExecutionPolicy Bypass -File scripts/git_upload.ps1
# 4. 按照提示输入 GitHub 仓库地址

param(
    [string]$RepoUrl = ""
)

Write-Host "=== ODPlatform Git 上传工具 ===" -ForegroundColor Cyan

# 如果没有提供仓库地址，提示用户输入
if (-not $RepoUrl) {
    $RepoUrl = Read-Host "请输入 GitHub 仓库地址 (如: https://github.com/username/odplatform.git)"
}

# 1. 初始化 Git
Write-Host "`n[1/5] 初始化 Git 仓库..." -ForegroundColor Yellow
git init
git config user.name "ODPlatform"
git config user.email "odplatform@example.com"

# 2. 添加文件
Write-Host "`n[2/5] 添加所有文件..." -ForegroundColor Yellow
git add .

# 3. 提交
Write-Host "`n[3/5] 提交代码..." -ForegroundColor Yellow
git commit -m "Initial commit: ODPlatform core code"

# 4. 设置远程仓库
Write-Host "`n[4/5] 设置远程仓库..." -ForegroundColor Yellow
git remote add origin $RepoUrl

# 5. 推送
Write-Host "`n[5/5] 推送到远程仓库..." -ForegroundColor Yellow
git branch -M main
git push -u origin main

Write-Host "`n=== 上传完成！ ===" -ForegroundColor Green
Write-Host "仓库地址: $RepoUrl" -ForegroundColor Cyan