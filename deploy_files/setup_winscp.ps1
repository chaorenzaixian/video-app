# Setup WinSCP for automated uploads
Write-Host "Installing WinSCP..." -ForegroundColor Yellow

# Download WinSCP portable
$winscp_url = "https://winscp.net/download/WinSCP-5.21.8-Portable.zip"
$download_path = "C:\Temp\winscp.zip"
$install_path = "C:\Program Files\WinSCP"

# Create temp directory
New-Item -ItemType Directory -Path "C:\Temp" -Force | Out-Null

# Download WinSCP
Write-Host "Downloading WinSCP..." -ForegroundColor Gray
Invoke-WebRequest -Uri $winscp_url -OutFile $download_path

# Extract
Write-Host "Extracting..." -ForegroundColor Gray
Expand-Archive -Path $download_path -DestinationPath $install_path -Force

# Clean up
Remove-Item $download_path -Force

Write-Host "WinSCP installed to: $install_path" -ForegroundColor Green
Write-Host "WinSCP.com path: $install_path\WinSCP.com" -ForegroundColor White
