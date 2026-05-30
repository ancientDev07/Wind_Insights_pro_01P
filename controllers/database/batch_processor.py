# controllers/database/batch_processor.py
import logging
from typing import Dict
import pandas as pd

class BatchProcessor:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def save_all_turbines(self, project_id: int, turbine_clusters: Dict[str, pd.DataFrame]):
        """Save all turbines in single transaction"""
        try:
            self.db_manager.begin_transaction()
            
            total = len(turbine_clusters)
            for idx, (wtg_id, turbine_data) in enumerate(turbine_clusters.items(), 1):
                self.db_manager.save_turbine_data(project_id, wtg_id, turbine_data)
                self.logger.info(f"Saved {idx}/{total}: {wtg_id} ({len(turbine_data)} rows)")
            
            self.db_manager.commit_transaction()
            return True
            
        except Exception as e:
            self.logger.error(f"Batch save failed: {e}")
            self.db_manager.rollback_transaction()
            raise
