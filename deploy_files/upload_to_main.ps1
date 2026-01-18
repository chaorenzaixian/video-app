# upload_to_main.ps1 - Upload using Python script
param(
    [Parameter(Mandatory=$true)]
    [string]$VideoFile
)

# Use Python script for upload
python D:\VideoTranscode\scripts\upload_simple.py $VideoFile
exit $LASTEXITCODE
