# ODPlatform 项目压缩脚本
# 使用方法：右键 -> 使用 PowerShell 运行

Write-Host "开始压缩 ODPlatform 项目..." -ForegroundColor Green

$SourcePath = "d:\od\ODPlatform"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$OutputPath = Join-Path $DesktopPath "ODPlatform_Package"
$ZipPath = Join-Path $DesktopPath "ODPlatform_Package.zip"

# 1. 删除不必要的文件夹
Write-Host "`n[1/4] 清理不必要的文件..." -ForegroundColor Yellow

$ItemsToRemove = @(
    "$SourcePath\.git",
    "$SourcePath\runs",
    "$SourcePath\logs",
    "$SourcePath\.pytest_cache",
    "$SourcePath\.adr"
)

foreach ($item in $ItemsToRemove) {
    if (Test-Path $item) {
        Write-Host "  删除: $item" -ForegroundColor Gray
        Remove-Item -Path $item -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# 2. 创建临时打包目录
Write-Host "`n[2/4] 创建打包目录..." -ForegroundColor Yellow
if (Test-Path $OutputPath) {
    Remove-Item -Path $OutputPath -Recurse -Force
}
New-Item -Path $OutputPath -ItemType Directory -Force | Out-Null

# 3. 复制必要文件
Write-Host "`n[3/4] 复制必要文件..." -ForegroundColor Yellow

$ItemsToCopy = @(
    "apps",
    "data",
    "models",
    "packages",
    "scripts",
    "tests",
    "docs",
    "README.md",
    "environment.yml"
)

foreach ($item in $ItemsToCopy) {
    $src = Join-Path $SourcePath $item
    $dst = Join-Path $OutputPath $item
    if (Test-Path $src) {
        Write-Host "  复制: $item" -ForegroundColor Gray
        Copy-Item -Path $src -Destination $dst -Recurse -Force
    }
}

# 4. 创建使用说明
Write-Host "`n[4/4] 创建使用说明..." -ForegroundColor Yellow
$Readme = @"
# ODPlatform 使用说明

## 快速开始

### 1. 安装 Miniconda
下载地址：https://docs.conda.io/en/latest/miniconda.html

### 2. 创建环境
打开 Anaconda Prompt (Miniconda3)，运行：
\`\`\`bash
cd ODPlatform_Package
conda env create -f environment.yml
conda activate odplatform-gpu
\`\`\`

### 3. 启动前端
\`\`\`bash
cd apps\desktop
python -m odp_desktop.main
\`\`\`

## 目录说明

- **apps/** - 应用程序代码
  - **desktop/** - 桌面应用前端
  - **platform/** - 核心平台后端
- **data/** - 数据集目录
- **models/** - 训练好的模型文件
- **scripts/** - 辅助脚本
- **tests/** - 测试代码

## 功能模块

1. **Train** - 训练模型
2. **Split** - 数据集划分
3. **Infer** - 推理检测

## 注意事项

- 确保有足够的磁盘空间（建议 10GB+）
- 训练需要 NVIDIA GPU（可选，但会加快速度）
- 首次运行需要下载 YOLO 预训练模型

---
创建时间: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@

$Readme | Out-File -FilePath (Join-Path $OutputPath "使用说明.md") -Encoding UTF8

# 计算大小
$size = (Get-ChildItem -Path $OutputPath -Recurse -File | Measure-Object -Property Length -Sum).Sum
$sizeGB = [math]::Round($size/1GB, 2)
Write-Host "`n打包完成！" -ForegroundColor Green
Write-Host "打包路径: $OutputPath" -ForegroundColor Cyan
Write-Host "打包大小: $sizeGB GB" -ForegroundColor Cyan
Write-Host "文件数量: $((Get-ChildItem -Path $OutputPath -Recurse -File).Count)" -ForegroundColor Cyan

# 询问是否压缩
$compress = Read-Host "`n是否压缩为 ZIP 文件？(y/n)"
if ($compress -eq "y") {
    Write-Host "正在压缩..." -ForegroundColor Yellow
    if (Test-Path $ZipPath) {
        Remove-Item $ZipPath -Force
    }
    Compress-Archive -Path $OutputPath -DestinationPath $ZipPath -CompressionLevel Optimal
    $zipSize = [math]::Round((Get-Item $ZipPath).Length/1GB, 2)
    Write-Host "压缩完成！" -ForegroundColor Green
    Write-Host "压缩文件: $ZipPath" -ForegroundColor Cyan
    Write-Host "压缩后大小: $zipSize GB" -ForegroundColor Cyan
}

Write-Host "`n完成！" -ForegroundColor Green
