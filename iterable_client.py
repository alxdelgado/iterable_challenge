"""
Iterable API Client Module
Handles API calls to Iterable users/update and events/track endpoints
Includes JWT authentication, retry/backoff logic, and CSV export
"""

import requests
import logging
import csv
import time
import jwt
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

logger = logging.getLogger(__name__)


class IterableClient:
    """Client for making API calls to Iterable endpoints with retry logic and JWT support"""

    def __init__(self, api_key: str = None, jwt_secret: str = None, use_jwt: bool = False, base_url: str = "https://api.iterable.com"):
        """
        Initialize Iterable API client

        Args:
            api_key: Iterable API key for authentication (if not using JWT)
            jwt_secret: JWT secret for generating authentication tokens
            use_jwt: Whether to use JWT authentication instead of API key
            base_url: Base URL for Iterable API (default: https://api.iterable.com)
        """
        self.api_key = api_key
        self.jwt_secret = jwt_secret
        self.use_jwt = use_jwt
        self.base_url = base_url.rstrip('/')
        
        # Rate limit tracking
        self.users_update_limit = 500  # requests/second
        self.events_track_limit = 2000  # requests/second
        
        # Retry configuration
        self.max_retries = 3
        self.backoff_factor = 2  # Exponential backoff multiplier
        self.initial_backoff = 1  # Initial backoff in seconds
        
        # Setup headers
        self._update_headers()

    def _update_headers(self) -> None:
        """Setup authentication headers based on authentication method"""
        self.headers = {
            'Content-Type': 'application/json'
        }
        
        if self.use_jwt and self.jwt_secret:
            # Generate JWT token
            token = self._generate_jwt_token()
            self.headers['Authorization'] = f'Bearer {token}'
            logger.info("Using JWT authentication")
        elif self.api_key:
            # Use API key
            self.headers['Api-Key'] = self.api_key
            logger.info("Using API key authentication")
        else:
            logger.warning("No authentication method configured")

    def _generate_jwt_token(self) -> str:
        """
        Generate JWT token for Iterable API authentication

        Returns:
            JWT token string
        """
        try:
            payload = {
                'iss': 'iterable-integration',
                'iat': int(time.time()),
                'exp': int(time.time()) + 3600  # Valid for 1 hour
            }
            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            logger.debug("JWT token generated successfully")
            return token
        except Exception as e:
            logger.error(f"Failed to generate JWT token: {e}")
            raise

    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff time for retry

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Backoff time in seconds
        """
        backoff_time = self.initial_backoff * (self.backoff_factor ** attempt)
        # Add jitter (random variation) to prevent thundering herd
        jitter = backoff_time * 0.1
        import random
        return backoff_time + random.uniform(-jitter, jitter)

    def _is_retryable(self, status_code: int) -> bool:
        """
        Determine if a request should be retried based on status code

        Args:
            status_code: HTTP status code

        Returns:
            True if request should be retried, False otherwise
        """
        # Retry on server errors and specific client errors
        retryable_codes = [408, 429, 500, 502, 503, 504]
        return status_code in retryable_codes

    def _handle_response(self, response: requests.Response, endpoint: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Handle API response and distinguish between success and error states

        Args:
            response: Response object from requests library
            endpoint: Name of endpoint called (for logging)

        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        response_data = {}
        
        try:
            response_data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response from {endpoint}: {e}")
            response_data = {'raw_response': response.text}

        # Check HTTP status code
        if response.status_code >= 500:
            logger.error(
                f"5xx Server Error from {endpoint}: Status {response.status_code}\n"
                f"Response: {response_data}"
            )
            return False, response_data
        elif response.status_code >= 400:
            logger.error(
                f"4xx Client Error from {endpoint}: Status {response.status_code}\n"
                f"Response: {response_data}"
            )
            return False, response_data
        elif response.status_code >= 200 and response.status_code < 300:
            # Check if response code indicates success
            code = response_data.get('code', 'Unknown')
            if code == 'Success':
                logger.info(f"{endpoint} call successful: {response_data.get('msg', 'Success')}")
                return True, response_data
            else:
                # HTTP 200 but API error code
                logger.warning(
                    f"{endpoint} returned HTTP 200 but error code: {code}\n"
                    f"Message: {response_data.get('msg', 'No message')}"
                )
                return False, response_data
        else:
            logger.warning(f"Unexpected status code from {endpoint}: {response.status_code}")
            return False, response_data

    def _make_request_with_retry(self, method: str, endpoint_url: str, payload: Dict[str, Any], endpoint_name: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Make HTTP request with exponential backoff retry logic

        Args:
            method: HTTP method (POST, GET, etc.)
            endpoint_url: Full URL for the endpoint
            payload: Request payload
            endpoint_name: Name of endpoint for logging

        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        last_exception = None
        last_response = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.max_retries} for {endpoint_name}")
                
                if method.upper() == 'POST':
                    response = requests.post(
                        endpoint_url,
                        json=payload,
                        headers=self.headers,
                        timeout=10
                    )
                else:
                    response = requests.get(
                        endpoint_url,
                        headers=self.headers,
                        timeout=10
                    )
                
                last_response = response
                
                # Check if successful
                if response.status_code < 400 or not self._is_retryable(response.status_code):
                    # Either success or non-retryable error
                    return self._handle_response(response, endpoint_name)
                
                # Retryable error - check if we should retry
                if attempt < self.max_retries - 1:
                    backoff_time = self._calculate_backoff(attempt)
                    logger.warning(
                        f"Retryable error {response.status_code} from {endpoint_name}. "
                        f"Retrying in {backoff_time:.2f}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(backoff_time)
                else:
                    logger.error(f"Max retries reached for {endpoint_name}")
                    return self._handle_response(response, endpoint_name)
                    
            except requests.exceptions.Timeout:
                last_exception = f"Timeout on attempt {attempt + 1}"
                logger.warning(f"Timeout from {endpoint_name}. Attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    backoff_time = self._calculate_backoff(attempt)
                    time.sleep(backoff_time)
            except requests.exceptions.RequestException as e:
                last_exception = str(e)
                logger.warning(f"Request exception from {endpoint_name}: {e}. Attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    backoff_time = self._calculate_backoff(attempt)
                    time.sleep(backoff_time)
        
        # All retries exhausted
        logger.error(f"All {self.max_retries} attempts failed for {endpoint_name}")
        return False, {'error': last_exception or 'Max retries exceeded'}

    def update_user(self, email: str, data_fields: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Update user profile in Iterable using users/update endpoint with retry logic

        Args:
            email: User email address (must provide email or userId)
            data_fields: Dictionary of user profile fields to update

        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        endpoint_url = f"{self.base_url}/api/users/update"
        
        payload = {
            'email': email,
            'dataFields': data_fields
        }

        logger.debug(f"Calling users/update for email: {email}")
        return self._make_request_with_retry('POST', endpoint_url, payload, 'users/update')

    def track_event(self, email: str, event_name: str, data_fields: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Track event in Iterable using events/track endpoint with retry logic

        Args:
            email: User email address (must provide email or userId)
            event_name: Name of event (e.g., 'page_view')
            data_fields: Dictionary of event-specific fields

        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        endpoint_url = f"{self.base_url}/api/events/track"
        
        payload = {
            'email': email,
            'eventName': event_name,
            'dataFields': data_fields
        }

        logger.debug(f"Calling events/track for email: {email}, event: {event_name}")
        return self._make_request_with_retry('POST', endpoint_url, payload, 'events/track')

    def process_user_record(self, user_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single user record by making both users/update and events/track calls

        Args:
            user_record: Dictionary containing user and page view data from Phase 2 Query 2

        Returns:
            Dictionary containing processing results and status
        """
        email = user_record.get('email')
        result = {
            'email': email,
            'timestamp': datetime.now().isoformat(),
            'users_update': {'success': False, 'response': {}},
            'events_track': {'success': False, 'response': {}},
            'overall_success': False
        }

        if not email:
            logger.error("User record missing email address")
            return result

        # Prepare dataFields for users/update
        user_data_fields = {
            'first_name': user_record.get('first_name'),
            'last_name': user_record.get('last_name'),
            'plan_type': user_record.get('plan_type'),
            'recent_page_view': True,
            'candidate': user_record.get('candidate')
        }

        # Call users/update
        logger.info(f"Processing user: {email}")
        update_success, update_response = self.update_user(email, user_data_fields)
        result['users_update'] = {
            'success': update_success,
            'response': update_response
        }

        # Prepare dataFields for events/track
        event_data_fields = {
            'page': user_record.get('page'),
            'browser': user_record.get('device'),
            'location': user_record.get('location'),
            'timestamp': str(user_record.get('event_time')),
            'candidate': user_record.get('candidate')
        }

        # Call events/track
        track_success, track_response = self.track_event(
            email,
            'page_view',
            event_data_fields
        )
        result['events_track'] = {
            'success': track_success,
            'response': track_response
        }

        # Overall success requires both calls to succeed
        result['overall_success'] = update_success and track_success

        if result['overall_success']:
            logger.info(f"✓ Successfully processed user: {email}")
        else:
            logger.warning(f"✗ Partial failure processing user: {email}")

        return result


def export_results_to_csv(user_records: List[Dict[str, Any]], filename: str = None) -> str:
    """
    Export SQL query results to CSV file

    Args:
        user_records: List of user records from Phase 2 Query 2
        filename: Output filename (if None, generates timestamped name)

    Returns:
        Path to the generated CSV file
    """
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"query_results_{timestamp}.csv"
    
    if not user_records:
        logger.warning("No records to export to CSV")
        return filename
    
    try:
        # Get all keys from first record to use as headers
        fieldnames = list(user_records[0].keys())
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(user_records)
        
        logger.info(f"Exported {len(user_records)} records to CSV: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Failed to export results to CSV: {e}")
        raise

