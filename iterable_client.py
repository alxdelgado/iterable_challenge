"""
Iterable API Client Module
Handles API calls to Iterable users/update and events/track endpoints
"""

import requests
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class IterableClient:
    """Client for making API calls to Iterable endpoints"""

    def __init__(self, api_key: str, base_url: str = "https://api.iterable.com"):
        """
        Initialize Iterable API client

        Args:
            api_key: Iterable API key for authentication
            base_url: Base URL for Iterable API (default: https://api.iterable.com)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Content-Type': 'application/json',
            'Api-Key': api_key
        }
        # Rate limit tracking
        self.users_update_limit = 500  # requests/second
        self.events_track_limit = 2000  # requests/second

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

    def update_user(self, email: str, data_fields: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Update user profile in Iterable using users/update endpoint

        Args:
            email: User email address (must provide email or userId)
            data_fields: Dictionary of user profile fields to update
                Expected: {first_name, last_name, plan_type, recent_page_view, candidate}

        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        endpoint_url = f"{self.base_url}/api/users/update"
        
        payload = {
            'email': email,
            'dataFields': data_fields
        }

        try:
            logger.debug(f"Calling users/update for email: {email}")
            response = requests.post(
                endpoint_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            success, response_data = self._handle_response(response, "users/update")
            
            if not success:
                logger.error(f"Failed to update user {email}. Response: {response_data}")
            
            return success, response_data
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling users/update for {email}")
            return False, {'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception calling users/update for {email}: {e}")
            return False, {'error': str(e)}

    def track_event(self, email: str, event_name: str, data_fields: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Track event in Iterable using events/track endpoint

        Args:
            email: User email address (must provide email or userId)
            event_name: Name of event (e.g., 'page_view')
            data_fields: Dictionary of event-specific fields
                Expected: {page, browser, location, timestamp, candidate}

        Returns:
            Tuple of (success: bool, response_data: dict)
        """
        endpoint_url = f"{self.base_url}/api/events/track"
        
        payload = {
            'email': email,
            'eventName': event_name,
            'dataFields': data_fields
        }

        try:
            logger.debug(f"Calling events/track for email: {email}, event: {event_name}")
            response = requests.post(
                endpoint_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            success, response_data = self._handle_response(response, "events/track")
            
            if not success:
                logger.error(f"Failed to track event for {email}. Response: {response_data}")
            
            return success, response_data
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling events/track for {email}")
            return False, {'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception calling events/track for {email}: {e}")
            return False, {'error': str(e)}

    def process_user_record(self, user_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single user record by making both users/update and events/track calls

        Args:
            user_record: Dictionary containing user and page view data from Phase 2 Query 2
                Expected keys: email, first_name, last_name, plan_type, candidate,
                              page, browser, location, event_time

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
            'browser': user_record.get('device'),  # Note: device in DB, browser in events
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
