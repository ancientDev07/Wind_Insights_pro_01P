# data/data_manager.py
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from sklearn.preprocessing import LabelEncoder
from datetime import datetime
from utils.logger import logger
from models import scada_utils as su

class DataManager:
    """
    Enhanced DataManager class for handling wind turbine data operations.
    Includes data validation, preprocessing, and memory optimization.
    """
    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.turbine_data: Dict[str, pd.DataFrame] = {}
        self.label_encoder = LabelEncoder()
        self.metadata: Dict[str, Any] = {
            'last_updated': None,
            'total_turbines': 0,
            'data_columns': [],
            'missing_values': {},
            'data_types': {}
        }

    def load_data(self, data: pd.DataFrame) -> bool:
        try:
            if not isinstance(data, pd.DataFrame):
                raise ValueError("Input must be a pandas DataFrame")
            if data.empty:
                raise ValueError("DataFrame is empty")

            self.data = data
            self._update_metadata()
            self._clean_data()
            self.optimize_data_types()  # Optimize data types after cleaning
            logger.info("Data loaded successfully")
            logger.info(f"Loaded {len(self.data)} rows and {len(self.data.columns)} columns")
            return True
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            self.data = None
            return False

    def _update_metadata(self):
        """Update metadata about the loaded data"""
        try:
            self.metadata.update({
                'last_updated': datetime.now(),
                'data_columns': list(self.data.columns),
                'missing_values': self.data.isnull().sum().to_dict(),
                'data_types': self.data.dtypes.to_dict(),
                'total_rows': len(self.data)
            })

            if 'Wtg' in self.data.columns:
                self.metadata['total_turbines'] = self.data['Wtg'].nunique()

            logger.info("Metadata updated successfully")

        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")

    def _clean_data(self):
        """Perform basic data cleaning operations"""
        try:
            if self.data is None or self.data.empty:
                raise ValueError("No data to clean")

            # Make a copy to avoid modifying the original data
            self.data = self.data.copy()

            # Remove completely empty rows and columns
            self.data.dropna(how='all', inplace=True)
            self.data.dropna(axis=1, how='all', inplace=True)

            # Convert column names to string and clean them
            self.data.columns = self.data.columns.astype(str).str.strip()

            # Handle infinite values
            self.data.replace([np.inf, -np.inf], np.nan, inplace=True)

            # Remove any duplicate columns
            self.data = self.data.loc[:, ~self.data.columns.duplicated()]

            # Try to convert numeric columns
            for col in self.data.columns:
                try:
                    # Check if the column might be numeric
                    if self.data[col].dtype == object:
                        # Replace common decimal separators
                        if isinstance(self.data[col].iloc[0], str):
                            self.data[col] = self.data[col].str.replace(',', '.')
                        # Try to convert to numeric
                        try:
                            converted = pd.to_numeric(self.data[col])
                            self.data[col] = converted
                        except (ValueError, TypeError):
                            # Try coercing invalid values to NaN
                            converted = pd.to_numeric(self.data[col], errors='coerce')
                            # Only replace if we successfully converted a significant portion
                            if converted.notna().sum() > len(self.data) * 0.8:  # 80% threshold
                                self.data[col] = converted
                except Exception as e:
                    logger.warning(f"Could not convert column {col} to numeric: {e}")
                    continue

            logger.info(f"Data cleaning completed successfully. Shape: {self.data.shape}")
            logger.info(f"Columns: {', '.join(self.data.columns)}")

        except Exception as e:
            logger.error(f"Error during data cleaning: {e}")
            raise

    def encode_turbine_ids(self) -> bool:
        """
        Identify and validate the turbine ID column, updating metadata.

        Returns:
        bool: True if turbine ID column was identified successfully, False otherwise.
        """
        try:
            if self.data is None:
                raise ValueError("No data loaded")

            # Find turbine ID column using scada_utils
            # matched_columns = su.find_matching_columns(self.data, 'turbine_id')

            # if not matched_columns:
            #     raise KeyError("No turbine ID column found in data")

            # turbine_col = matched_columns[0]  # Use the first matched column

            # NEW:
            from models.scada_utils import detect_turbine_column
            turbine_col = detect_turbine_column(self.data)
            if not turbine_col:
                raise KeyError("No turbine ID column found in data")

            # Convert turbine column to string type for consistency
            self.data[turbine_col] = self.data[turbine_col].astype(str)

            # Update metadata
            self.metadata['turbine_column'] = turbine_col
            self.metadata['total_turbines'] = self.data[turbine_col].nunique()

            logger.info(f"Turbine ID column identified: {turbine_col}")
            logger.info(f"Found {self.metadata['total_turbines']} unique turbines")
            return True

        except Exception as e:
            logger.error(f"Failed to identify turbine ID column: {e}")
            return False

    def get_turbine_data(self, turbine_id: str) -> Optional[pd.DataFrame]:
        """
        Get data for a specific turbine with validation.

        Parameters:
        turbine_id (str): The turbine identifier.

        Returns:
        Optional[pd.DataFrame]: DataFrame containing turbine data or None if not found.
        """
        try:
            if self.data is None:
                raise ValueError("No data loaded")

            if 'Wtg' not in self.data.columns:
                raise KeyError("Column 'Wtg' not found in data")

            # Convert turbine_id to string for consistent comparison
            turbine_id = str(turbine_id)
            
            # Get turbine data
            turbine_data = self.data[self.data['Wtg'] == turbine_id].copy()
            
            if turbine_data.empty:
                logger.warning(f"No data found for turbine {turbine_id}")
                return None

            return turbine_data

        except Exception as e:
            logger.error(f"Error retrieving turbine data: {e}")
            return None

    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the loaded data.

        Returns:
        Dict[str, Any]: Dictionary containing data summary.
        """
        if self.data is None:
            return {'error': 'No data loaded'}

        try:
            summary = {
                'total_rows': len(self.data),
                'total_columns': len(self.data.columns),
                'total_turbines': self.metadata.get('total_turbines', 0),
                'columns': list(self.data.columns),
                'missing_values': self.metadata.get('missing_values', {}),
                'last_updated': self.metadata.get('last_updated')
            }
            return summary

        except Exception as e:
            logger.error(f"Error generating data summary: {e}")
            return {'error': str(e)}

    def clear_data(self):
        """Safely clear all data and reset the manager"""
        try:
            self.data = None
            self.turbine_data.clear()
            self.label_encoder = LabelEncoder()
            self.metadata = {
                'last_updated': None,
                'total_turbines': 0,
                'data_columns': [],
                'missing_values': {},
                'data_types': {}
            }
            logger.info("DataManager reset successfully")

        except Exception as e:
            logger.error(f"Error clearing data: {e}")
    
    def read_csv_safe(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Safely read CSV files with error handling and auto-detection of parameters

        Parameters:
        file_path (str): Path to the CSV file
        **kwargs: Additional parameters to pass to pd.read_csv

        Returns:
        pd.DataFrame: The loaded data
        """
        try:
            from utils.csv_handler import CSVConfig
            csv_config = CSVConfig(self)  # Use self as config since we have the necessary defaults
            
            # Get CSV parameters with automatic detection
            params = csv_config.get_csv_params(file_path)
            params.update(kwargs)  # Allow overriding of auto-detected parameters
            
            try:
                # First attempt with strict parsing
                return pd.read_csv(
                    file_path,
                    **params,
                    low_memory=False,  # Prevent mixed type inference warnings
                    dtype_backend='numpy_nullable'  # Use nullable types for better memory usage
                )
            except pd.errors.ParserError as e:
                logger.warning(f"Parser error with strict mode: {e}")
                # Retry with more lenient parsing
                params['on_bad_lines'] = 'skip'
                return pd.read_csv(
                    file_path,
                    **params,
                    low_memory=False,
                    dtype_backend='numpy_nullable'
                )
                
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {str(e)}")
            raise

    # Enhanced version of optimize_data_types in DataManager
    def optimize_data_types(self):
        if self.data is None:
            return
        
        # Track memory usage before optimization
        initial_memory = self.data.memory_usage(deep=True).sum()
        
        for col in self.data.columns:
            # Convert object columns with low cardinality to category
            if self.data[col].dtype == 'object':
                num_unique = self.data[col].nunique()
                if num_unique < len(self.data) * 0.5:  # If less than 50% unique values
                    self.data[col] = self.data[col].astype('category')
            
            # Downcast numeric columns
            elif pd.api.types.is_integer_dtype(self.data[col]):
                self.data[col] = pd.to_numeric(self.data[col], downcast='integer')
            elif pd.api.types.is_float_dtype(self.data[col]):
                self.data[col] = pd.to_numeric(self.data[col], downcast='float')
        
        # Track memory savings
        final_memory = self.data.memory_usage(deep=True).sum()
        savings = (1 - final_memory/initial_memory) * 100
        logger.info(f"Memory optimization complete. Saved {savings:.1f}% memory")