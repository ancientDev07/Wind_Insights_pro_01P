import pandas as pd

class SchemaDetector:
    def detect_wtg_column(self, df):
        patterns = ['wtg', 'turbine', 'id']
        
        for col in df.columns:
            if col.lower() in patterns:
                return col
        
        for col in df.columns:
            if df[col].astype(str).str.contains('WTG|T0', na=False).any():
                return col
        return None
    
    def cluster_by_turbine(self, df, wtg_column):
        if wtg_column:
            return {str(wtg): group for wtg, group in df.groupby(wtg_column)}
        else:
            return {"WTG_01": df}
