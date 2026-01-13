"""
Iterable Integration Main Script
Orchestrates database queries and Iterable API calls with error handling and logging
"""

import os
import sys
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from datetime import datetime

# Import modules
from db_connection import DatabaseConnection
from iterable_client import IterableClient
from logger_config import setup_logger, get_logger

# Initialize logger
load_dotenv()
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_file = os.getenv('LOG_FILE', 'iterable_integration.log')
logger = setup_logger(__name__, log_file=log_file, log_level=log_level)


def load_environment_variables() -> Dict[str, str]:
    """
    Load and validate environment variables from .env file

    Returns:
        Dictionary of environment variables
    """
    required_vars = [
        'DB_HOST',
        'DB_USER',
        'DB_PASSWORD',
        'DB_NAME',
        'ITERABLE_API_KEY'
    ]
    
    env_vars = {}
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            env_vars[var] = value
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please ensure .env file is configured with all required variables")
        sys.exit(1)
    
    logger.info("Environment variables loaded successfully")
    return env_vars


def run_integration():
    """
    Main integration workflow:
    1. Load configuration from .env
    2. Connect to database
    3. Execute Phase 2 Query 2 to get pro users with recent engagement
    4. For each user, make users/update and events/track API calls to Iterable
    5. Log all results
    """
    
    logger.info("=" * 70)
    logger.info("Starting Iterable Integration - Phase 3")
    logger.info("=" * 70)
    
    # Step 1: Load environment variables
    logger.info("\n[STEP 1] Loading environment variables...")
    try:
        env_vars = load_environment_variables()
    except SystemExit:
        return
    
    # Step 2: Connect to database
    logger.info("\n[STEP 2] Connecting to database...")
    db = DatabaseConnection(
        host=env_vars['DB_HOST'],
        user=env_vars['DB_USER'],
        password=env_vars['DB_PASSWORD'],
        database=env_vars['DB_NAME']
    )
    
    if not db.connect():
        logger.error("Failed to connect to database. Exiting.")
        return
    
    # Step 3: Execute Phase 2 Query 2
    logger.info("\n[STEP 3] Executing Phase 2 Query 2: Get pro users with recent engagement...")
    user_records = db.get_pro_users_recent_engagement()
    
    if not user_records:
        logger.warning("No pro users with recent pricing/settings page views found")
        db.disconnect()
        return
    
    logger.info(f"Found {len(user_records)} pro user(s) with recent engagement")
    
    # Step 4: Initialize Iterable client
    logger.info("\n[STEP 4] Initializing Iterable API client...")
    iterable_client = IterableClient(
        api_key=env_vars['ITERABLE_API_KEY'],
        base_url=os.getenv('ITERABLE_API_BASE_URL', 'https://api.iterable.com')
    )
    logger.info("Iterable API client initialized")
    
    # Step 5: Process each user record
    logger.info("\n[STEP 5] Processing user records...")
    logger.info("-" * 70)
    
    results = {
        'total_users': len(user_records),
        'successful': 0,
        'partial_failures': 0,
        'total_failures': 0,
        'records': []
    }
    
    for index, user_record in enumerate(user_records, 1):
        logger.info(f"\nProcessing record {index}/{len(user_records)}")
        
        # Process user and make API calls
        process_result = iterable_client.process_user_record(user_record)
        results['records'].append(process_result)
        
        # Update statistics
        if process_result['overall_success']:
            results['successful'] += 1
        elif process_result['users_update']['success'] or process_result['events_track']['success']:
            results['partial_failures'] += 1
        else:
            results['total_failures'] += 1
    
    # Step 6: Disconnect and summarize
    logger.info("\n" + "-" * 70)
    logger.info("\n[STEP 6] Generating summary report...")
    
    db.disconnect()
    
    # Log summary
    logger.info("\n" + "=" * 70)
    logger.info("INTEGRATION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total users processed: {results['total_users']}")
    logger.info(f"✓ Successful (both API calls): {results['successful']}")
    logger.info(f"⚠ Partial failures (one call failed): {results['partial_failures']}")
    logger.info(f"✗ Total failures (both calls failed): {results['total_failures']}")
    logger.info("=" * 70)
    
    # Save detailed results to JSON file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"integration_results_{timestamp}.json"
    
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"\nDetailed results saved to: {results_file}")
    except Exception as e:
        logger.error(f"Failed to save results to file: {e}")
    
    logger.info("\nIntegration complete!")


def main():
    """Entry point for the script"""
    try:
        run_integration()
    except KeyboardInterrupt:
        logger.info("\n\nIntegration interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Unexpected error during integration: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
