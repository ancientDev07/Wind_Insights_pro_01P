# PROJECT ID CONNECTION ISSUE - DEBUGGING & LEARNING NOTES

**Date:** December 31, 2024  
**Issue:** Project ID not passing to sub-applications (PowerCurveWindow, etc.)  
**Status:** ✅ RESOLVED

---

## 🔍 PROBLEM SUMMARY

Sub-applications (PowerCurveWindow, VisualizationWindow, etc.) were not receiving `project_id`, causing:
- Unable to load coordinate data from database
- Unable to load AD reference data from database
- Air Density correction failing
- Database queries returning empty results

---

## 🐛 ROOT CAUSES IDENTIFIED

### **1. Duplicate ControlPanel Instances**
**Location:** `WWIP_APP.py` + `views/components/home/right_side_bar.py`

**Problem:**
```python
# WWIP_APP.py line 107
self.control_panel = ControlPanel(self, self.file_handler, project_id=self.current_project_id)
# ↑ This instance gets project_id updated ✓

# WWIP_APP.py line 115
self.right_side_bar = RightSideBar(self, self.file_handler)
# ↑ Creates ANOTHER ControlPanel inside (project_id=None) ✗

# right_side_bar.py line 28
control_panel = ControlPanel(self, file_handler)  # NEW INSTANCE!

Impact: User interacts with RightSideBar's ControlPanel which never receives project_id.

Fix: Remove RightSideBar, use only control_panel_dock.