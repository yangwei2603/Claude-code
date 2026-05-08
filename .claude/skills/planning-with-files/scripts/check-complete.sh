#!/bin/bash
# Check if task is truly complete before stopping

if [ -f "task_plan.md" ]; then
    echo "[planning-with-files] Checking task completion..."
    
    # Count pending and in_progress phases
    pending=$(grep -c "Status:.*pending" task_plan.md 2>/dev/null || echo 0)
    in_progress=$(grep -c "Status:.*in_progress" task_plan.md 2>/dev/null || echo 0)
    
    if [ "$pending" -gt 0 ] || [ "$in_progress" -gt 0 ]; then
        echo "⚠️  WARNING: Task may not be complete!"
        echo "   Pending phases: $pending"
        echo "   In-progress phases: $in_progress"
        echo "   Review task_plan.md before finishing."
        exit 1
    else
        echo "✅ All phases marked complete."
    fi
fi

exit 0
