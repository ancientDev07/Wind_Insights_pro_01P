import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import pandas as pd
from utils.logger import logger

def save_csv(dataframe, file_path):
    """
    Save a DataFrame to a CSV file.

    Parameters:
    dataframe (pd.DataFrame): The DataFrame to save.
    file_path (str): The path to save the CSV file.
    """
    try:
        dataframe.to_csv(file_path, index=False)
        logger.info(f"CSV saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save CSV to {file_path}: {e}")
        show_error_message("Error", f"Failed to save CSV to {file_path}: {e}")

def get_directory_path(title):
    """
    Open a dialog to select a directory.

    Parameters:
    title (str): The title of the dialog.

    Returns:
    str: The selected directory path, or None if the user cancels.
    """
    options = QFileDialog.Options()
    options |= QFileDialog.ShowDirsOnly
    directory = QFileDialog.getExistingDirectory(None, title, options=options)
    if directory:
        logger.info(f"Selected directory: {directory}")
        return directory
    else:
        logger.info("No directory selected")
        return None

def show_error_message(title, message):
    """
    Show an error message dialog.

    Parameters:
    title (str): The title of the dialog.
    message (str): The error message to display.
    """
    QMessageBox.critical(None, title, message)
    logger.error(f"{title}: {message}")

def show_info_message(title, message):
    """
    Show an information message dialog.

    Parameters:
    title (str): The title of the dialog.
    message (str): The information message to display.
    """
    QMessageBox.information(None, title, message)
    logger.info(f"{title}: {message}")