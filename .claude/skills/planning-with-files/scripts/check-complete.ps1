# Check if task is truly complete before stopping

if (Test-Path "task_plan.md") {
    Write-Host "[planning-with-files] Checking task completion..."
    
    $content = Get-Content "task_plan.md" -Raw
    $pending = ([regex]::Matches($content, "Status:.*pending")).Count
    $inProgress = ([regex]::Matches($content, "Status:.*in_progress")).Count
    
    if ($pending -gt 0 -or $inProgress -gt 0) {
        Write-Host "⚠️  WARNING: Task may not be complete!" -ForegroundColor Yellow
        Write-Host "   Pending phases: $pending"
        Write-Host "   In-progress phases: $inProgress"
        Write-Host "   Review task_plan.md before finishing."
        exit 1
    } else {
        Write-Host "✅ All phases marked complete." -ForegroundColor Green
    }
}

exit 0
