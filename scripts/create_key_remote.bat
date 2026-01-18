@echo off
echo ========================================
echo Creating SSH Key on Transcode Server
echo ========================================
echo.

echo Step 1: Creating key file...
echo y | C:\Windows\System32\OpenSSH\ssh.exe -o StrictHostKeyChecking=no Administrator@198.176.60.121 "echo -----BEGIN OPENSSH PRIVATE KEY----- > C:\server_key && echo b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW >> C:\server_key && echo QyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gAAAAJDvzGZC78xm >> C:\server_key && echo QgAAAAtzc2gtZWQyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gA >> C:\server_key && echo AAAECtAxcJq0SjnZjz4DYebdKR/2BX09k3EOCZniP9JI0SwkT29AuLWcZ9YFVpwDKYl38H >> C:\server_key && echo pN5JWrop5jFkEJ3nsv2AAAAADXJvb3RASEIxMzExMDM= >> C:\server_key && echo -----END OPENSSH PRIVATE KEY----- >> C:\server_key"

echo.
echo Step 2: Verifying key file...
echo y | C:\Windows\System32\OpenSSH\ssh.exe -o StrictHostKeyChecking=no Administrator@198.176.60.121 "dir C:\server_key"

echo.
echo ========================================
echo Done!
echo ========================================
echo.
pause
