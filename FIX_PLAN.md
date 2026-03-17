# Fix Plan: Sidebar Toggle and Messaging Pane Resizing Issue

## Problem Analysis
The three-pin sidebar toggle button is causing the messaging pane to resize incorrectly when the sidebar is toggled open/closed.

## Root Cause
The issue appears to be in the CSS layout and transitions. The current implementation uses:
- `.main-content` with `margin-left: 280px`
- `.main-content.expanded` with `margin-left: 0`
- `.sidebar.collapsed` with `transform: translateX(-280px)`

However, there might be issues with:
1. Transition timing or properties
2. CSS specificity issues
3. Layout calculation problems

## Proposed Solution
1. **Fix CSS Transitions**: Ensure smooth transitions for both sidebar and main content
2. **Improve Layout Structure**: Use more reliable layout techniques
3. **Test Responsive Behavior**: Ensure it works across different screen sizes

## Steps to Fix
1. Update the CSS transitions for better performance
2. Add proper transition timing and easing
3. Test the fix on different screen sizes
4. Verify the messaging pane resizes correctly

## Files to Modify
- `templates/test.html` (CSS and JavaScript sections)
- `templates/about.html` (CSS section)
- `templates/terms.html` (CSS section)

## Expected Behavior
- When sidebar is toggled open: messaging pane should decrease in width
- When sidebar is toggled closed: messaging pane should increase in width
- Transitions should be smooth and consistent
