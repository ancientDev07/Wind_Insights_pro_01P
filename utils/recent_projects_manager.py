import os
import json
from datetime import datetime
from PyQt5.QtCore import QSettings
from typing import List, Dict, Optional

class RecentProjectsManager:
    """Unified recent projects manager for consistent data across the application"""
    
    def __init__(self):
        self.settings = QSettings("WindDataInsightPro", "ProjectManager")
        self._cleanup_old_files()
    
    def _cleanup_old_files(self):
        """Remove old JSON-based recent projects file"""
        old_file = os.path.join(os.path.expanduser("~"), ".wind_insight_recent.json")
        if os.path.exists(old_file):
            try:
                os.remove(old_file)
            except:
                pass
    
    def get_recent_projects(self) -> List[Dict]:
        """Get recent projects with full metadata"""
        recent_paths = self.settings.value("recent_projects", [])
        if not isinstance(recent_paths, list):
            recent_paths = []
        
        projects = []
        valid_paths = []
        
        for path in recent_paths:
            if os.path.exists(path):
                project_info = self._get_project_info(path)
                if project_info:
                    projects.append(project_info)
                    valid_paths.append(path)
        
        # Update settings with valid paths only
        if len(valid_paths) != len(recent_paths):
            self.settings.setValue("recent_projects", valid_paths)
            self.settings.sync()
        
        return projects[:10]  # Limit to 10
    
    def _get_project_info(self, project_path: str) -> Optional[Dict]:
        """Extract project information from file"""
        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            metadata = project_data.get("metadata", {})
            file_stat = os.stat(project_path)
            
            return {
                'path': project_path,
                'name': metadata.get("name", os.path.splitext(os.path.basename(project_path))[0]),
                'location': metadata.get("location", os.path.dirname(project_path)),
                'author': metadata.get("author", "Unknown"),
                'description': metadata.get("description", ""),
                'created_date': metadata.get("created_date", ""),
                'last_modified': metadata.get("last_modified", ""),
                'file_size': file_stat.st_size,
                'file_modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            }
        except Exception as e:
            return {
                'path': project_path,
                'name': f"⚠️ {os.path.basename(project_path)}",
                'location': "Error",
                'author': "Error",
                'description': f"Error: {str(e)}",
                'created_date': "",
                'last_modified': "",
                'file_size': 0,
                'file_modified': "",
                'error': True
            }
    
    def add_recent_project(self, project_path: str):
        """Add project to recent list"""
        recent = self.settings.value("recent_projects", [])
        if not isinstance(recent, list):
            recent = []
        
        # Remove if exists and add to front
        if project_path in recent:
            recent.remove(project_path)
        recent.insert(0, project_path)
        
        # Save limited list
        self.settings.setValue("recent_projects", recent[:10])
        self.settings.sync()
    
    def remove_recent_project(self, project_path: str):
        """Remove project from recent list"""
        recent = self.settings.value("recent_projects", [])
        if isinstance(recent, list) and project_path in recent:
            recent.remove(project_path)
            self.settings.setValue("recent_projects", recent)
            self.settings.sync()
    
    def clear_recent_projects(self):
        """Clear all recent projects"""
        self.settings.setValue("recent_projects", [])
        self.settings.sync()
