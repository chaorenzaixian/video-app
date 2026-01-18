# watcher.ps1 - Video transcoding monitor with auto-upload
$w="D:\VideoTranscode\downloads"
$p="D:\VideoTranscode\processing"
$c="D:\VideoTranscode\completed"
$logFile="D:\VideoTranscode\logs\watcher.log"

function Write-Log {
    param($Message, $Color="White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    $logMessage | Out-File -FilePath $logFile -Append
    Write-Host $logMessage -ForegroundColor $Color
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Video Transcoding Monitor Service (D drive)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Watch folder: $w" -ForegroundColor White
Write-Host "Processing folder: $p" -ForegroundColor White
Write-Host "Completed folder: $c" -ForegroundColor White
Write-Host "Log file: $logFile" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

Write-Log "Monitor service started (D drive)" "Green"

$processedCount = 0
$failedCount = 0
$uploadedCount = 0

while ($true) {
    try {
        $videos = Get-ChildItem -Path $w -Filter *.mp4 -ErrorAction SilentlyContinue
        
        if ($videos.Count -gt 0) {
            Write-Log "Found $($videos.Count) videos to process" "Yellow"
        }
        
        foreach ($f in $videos) {
            Write-Log "==========================================" "Cyan"
            Write-Log "Processing: $($f.Name)" "Cyan"
            
            # Move to processing folder
            $pp = Join-Path $p $f.Name
            try {
                Move-Item -Path $f.FullName -Destination $pp -Force
                Write-Log "Moved to processing folder" "Gray"
            } catch {
                Write-Log "Failed to move file: $_" "Red"
                continue
            }
            
            # Generate output filename
            $on = $f.BaseName + "_transcoded.mp4"
            $op = Join-Path $c $on
            
            # Transcode
            Write-Log "Starting transcode..." "Yellow"
            $transcodeStart = Get-Date
            
            & "D:\VideoTranscode\scripts\transcode.ps1" -InputFile $pp -OutputFile $op
            
            $transcodeEnd = Get-Date
            $transcodeDuration = ($transcodeEnd - $transcodeStart).TotalSeconds
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Transcode successful, duration: $([math]::Round($transcodeDuration, 2)) seconds" "Green"
                $processedCount++
                
                # Delete original file
                Remove-Item -Path $pp -Force
                Write-Log "Deleted original file" "Gray"
                
                # Upload to main server
                Write-Log "Uploading to main server..." "Yellow"
                $uploadStart = Get-Date
                
                & "D:\VideoTranscode\scripts\upload_to_main.ps1" -VideoFile $op
                
                $uploadEnd = Get-Date
                $uploadDuration = ($uploadEnd - $uploadStart).TotalSeconds
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "Upload successful, duration: $([math]::Round($uploadDuration, 2)) seconds" "Green"
                    $uploadedCount++
                    
                    # Optionally delete local file after successful upload
                    # Remove-Item -Path $op -Force
                    # Write-Log "Deleted local file after upload" "Gray"
                } else {
                    Write-Log "Upload failed, file kept locally: $op" "Red"
                }
                
                Write-Log "Video processing complete: $on" "Green"
                Write-Log "Total processed: $processedCount, failed: $failedCount, uploaded: $uploadedCount" "White"
            } else {
                Write-Log "Transcode failed" "Red"
                $failedCount++
                
                # Move failed file back to downloads
                Move-Item -Path $pp -Destination $f.FullName -Force -ErrorAction SilentlyContinue
            }
            
            Write-Log "==========================================" "Cyan"
            Write-Host ""
        }
        
        # Wait 10 seconds before next check
        Start-Sleep -Seconds 10
        
    } catch {
        Write-Log "Monitor service exception: $_" "Red"
        Start-Sleep -Seconds 30
    }
}
