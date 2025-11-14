"""
Error handling and logging for the cc Agents system.
Provides clear, actionable error messages to users.
"""

import sys
import traceback
import logging
from typing import Optional, Dict, Any
from enum import Enum

class ErrorType(Enum):
    """Types of errors that can occur."""
    DATABASE_CONNECTION = "database_connection"
    VALIDATION = "validation"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    UNKNOWN = "unknown"

class ErrorHandler:
    """Handles errors with clear, actionable messages."""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('cc_agents.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Handle an error with appropriate logging and user messaging."""
        error_type = self._classify_error(error)
        
        # Log the full error for debugging
        self.logger.error(f"Error occurred: {str(error)}", exc_info=True)
        
        # Get user-friendly message
        user_message = self._get_user_message(error, error_type, context)
        
        # Print user-friendly message
        print(f"\n❌ {user_message}")
        
        # Print additional context if available
        if context:
            print(f"\n📋 Context:")
            for key, value in context.items():
                print(f"   {key}: {value}")
        
        # Print troubleshooting tips
        troubleshooting = self._get_troubleshooting_tips(error_type, context)
        if troubleshooting:
            print(f"\n💡 Troubleshooting:")
            for tip in troubleshooting:
                print(f"   • {tip}")
        
        # Exit with appropriate code
        sys.exit(1)
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify the type of error."""
        error_str = str(error).lower()
        
        if any(word in error_str for word in ['connection', 'database', 'postgresql']):
            return ErrorType.DATABASE_CONNECTION
        elif any(word in error_str for word in ['validation', 'invalid', 'required']):
            return ErrorType.VALIDATION
        elif any(word in error_str for word in ['file', 'not found', 'no such file']):
            return ErrorType.FILE_NOT_FOUND
        elif any(word in error_str for word in ['permission', 'access', 'denied']):
            return ErrorType.PERMISSION
        elif any(word in error_str for word in ['config', 'environment', 'env']):
            return ErrorType.CONFIGURATION
        elif any(word in error_str for word in ['network', 'timeout', 'connection refused']):
            return ErrorType.NETWORK
        else:
            return ErrorType.UNKNOWN
    
    def _get_user_message(self, error: Exception, error_type: ErrorType, context: Optional[Dict[str, Any]]) -> str:
        """Get a user-friendly error message."""
        base_message = str(error)
        
        if error_type == ErrorType.DATABASE_CONNECTION:
            return f"Database connection failed: {base_message}\n\nThis usually means:\n• Database is not running\n• Connection credentials are incorrect\n• Network connectivity issues"
        
        elif error_type == ErrorType.VALIDATION:
            return f"Validation error: {base_message}\n\nPlease check your input parameters and try again."
        
        elif error_type == ErrorType.FILE_NOT_FOUND:
            return f"File not found: {base_message}\n\nThis usually means:\n• The agent/workflow doesn't exist\n• File permissions are incorrect\n• Path is wrong"
        
        elif error_type == ErrorType.PERMISSION:
            return f"Permission denied: {base_message}\n\nThis usually means:\n• Insufficient file permissions\n• Database access denied\n• Network access restricted"
        
        elif error_type == ErrorType.CONFIGURATION:
            return f"Configuration error: {base_message}\n\nThis usually means:\n• Missing environment variables\n• Incorrect configuration\n• Missing required files"
        
        elif error_type == ErrorType.NETWORK:
            return f"Network error: {base_message}\n\nThis usually means:\n• Network connectivity issues\n• Firewall blocking connection\n• Service unavailable"
        
        else:
            return f"An unexpected error occurred: {base_message}\n\nPlease check the logs for more details."
    
    def _get_troubleshooting_tips(self, error_type: ErrorType, context: Optional[Dict[str, Any]]) -> list:
        """Get troubleshooting tips based on error type."""
        tips = []
        
        if error_type == ErrorType.DATABASE_CONNECTION:
            tips.extend([
                "Check that PostgreSQL is running: `brew services list | grep postgresql`",
                "Verify your database connection in `local.env`",
                "Test connection: `psql $PG_DATABASE_URL`",
                "Check network connectivity to database host"
            ])
        
        elif error_type == ErrorType.VALIDATION:
            tips.extend([
                "Run `python -m src.cli --help` to see valid options",
                "Check that all required parameters are provided",
                "Verify scope values: SYSTEM or COMMON_BACKGROUND",
                "Ensure agent/workflow names are valid"
            ])
        
        elif error_type == ErrorType.FILE_NOT_FOUND:
            tips.extend([
                "Run `python -m src.cli agent list` to see available agents",
                "Run `python -m src.cli workflow list` to see available workflows",
                "Check that files exist in `definitions/` directory",
                "Verify file permissions: `ls -la definitions/`"
            ])
        
        elif error_type == ErrorType.PERMISSION:
            tips.extend([
                "Check file permissions: `ls -la definitions/`",
                "Check database permissions",
                "Try running with elevated permissions if needed",
                "Verify user has access to database"
            ])
        
        elif error_type == ErrorType.CONFIGURATION:
            tips.extend([
                "Check that `local.env` exists and is properly configured",
                "Verify all required environment variables are set",
                "Run `python -m src.test_system` to test configuration",
                "Check that all required Python packages are installed"
            ])
        
        elif error_type == ErrorType.NETWORK:
            tips.extend([
                "Check network connectivity: `ping <host>`",
                "Verify firewall settings",
                "Check VPN connection if applicable",
                "Try again in a few minutes"
            ])
        
        # Add general tips
        tips.extend([
            "Check the log file: `tail -f cc_agents.log`",
            "Run with verbose logging for more details",
            "Try the operation with a smaller scope first"
        ])
        
        return tips
    
    def log_operation_start(self, operation: str, context: Dict[str, Any] = None):
        """Log the start of an operation."""
        message = f"Starting operation: {operation}"
        if context:
            message += f" with context: {context}"
        self.logger.info(message)
    
    def log_operation_success(self, operation: str, result: Any = None):
        """Log successful completion of an operation."""
        message = f"Successfully completed: {operation}"
        if result:
            message += f" with result: {result}"
        self.logger.info(message)
    
    def log_operation_failure(self, operation: str, error: Exception):
        """Log failure of an operation."""
        self.logger.error(f"Failed to complete: {operation} - {str(error)}")
    
    def validate_environment(self) -> bool:
        """Validate that the environment is properly configured."""
        import os
        from dotenv import load_dotenv
        
        # Check if local.env exists
        if not os.path.exists('local.env'):
            print("❌ Configuration file 'local.env' not found")
            print("💡 Please create local.env with your database configuration")
            return False
        
        # Load environment variables
        load_dotenv('local.env')
        
        # Check required environment variables
        required_vars = ['PG_DATABASE_URL']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("💡 Please set these variables in your local.env file")
            return False
        
        return True

# Global error handler instance
error_handler = ErrorHandler() 