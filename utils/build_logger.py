# utils/build_logger.py
import sys
from datetime import datetime
from pathlib import Path

class BuildLogger:
    def __init__(self, log_to_file=True):
        self.log_to_file = log_to_file
        self.log_file = None
        if log_to_file:
            logs_dir = Path(__file__).parent.parent / 'logs'
            logs_dir.mkdir(exist_ok=True)
            self.log_file = logs_dir / f'build_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            
    def log(self, message, level='INFO'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f'[{timestamp}] {level}: {message}'
        
        # Print to console
        if level == 'ERROR':
            print(log_message, file=sys.stderr)
        else:
            print(log_message)
            
        # Write to log file
        if self.log_to_file and self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')

    def info(self, message):
        self.log(message, 'INFO')

    def warning(self, message):
        self.log(message, 'WARNING')

    def error(self, message):
        self.log(message, 'ERROR')

    def success(self, message):
        self.log(message, 'SUCCESS')
