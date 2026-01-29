"""
GitHub Copilot API Client

A client for making requests to the GitHub Copilot API.
This is designed to be a drop-in replacement for OpenAI client usage.
"""

import requests
import json
from typing import Optional, Dict, Any, List


class CopilotAPIError(Exception):
    """Exception raised for Copilot API errors."""
    def __init__(self, message: str, status_code: int = None, response: str = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class Message:
    """Represents a chat message."""
    def __init__(self, content: str, role: str = "assistant"):
        self.content = content
        self.role = role


class Choice:
    """Represents a choice in the API response."""
    def __init__(self, message: Message, finish_reason: str = "stop", index: int = 0):
        self.message = message
        self.finish_reason = finish_reason
        self.index = index


class ChatCompletion:
    """Represents a chat completion response."""
    def __init__(self, choices: List[Choice], model: str, usage: Dict = None):
        self.choices = choices
        self.model = model
        self.usage = usage or {}


class CopilotClient:
    """
    Client for the GitHub Copilot API.
    
    Usage:
        client = CopilotClient(api_key="ghp_...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.choices[0].message.content)
    """
    
    API_ENDPOINT = "https://api.githubcopilot.com/chat/completions"
    
    def __init__(self, api_key: str):
        """
        Initialize the Copilot client.
        
        Args:
            api_key: GitHub Personal Access Token (PAT) with Copilot access
        """
        self.api_key = api_key
        self.chat = self.Chat(self)
    
    class Chat:
        """Chat API namespace."""
        def __init__(self, client):
            self.client = client
            self.completions = self.Completions(client)
        
        class Completions:
            """Chat completions API."""
            def __init__(self, client):
                self.client = client
            
            def create(
                self,
                model: str,
                messages: List[Dict[str, str]],
                temperature: float = 1.0,
                max_tokens: Optional[int] = None,
                response_format: Optional[Dict] = None,
                **kwargs
            ) -> ChatCompletion:
                """
                Create a chat completion.
                
                Args:
                    model: The model to use (e.g., 'gpt-4o-mini', 'gpt-3.5-turbo')
                    messages: List of message dicts with 'role' and 'content'
                    temperature: Sampling temperature (0-2)
                    max_tokens: Maximum tokens in response
                    response_format: Optional format specification (e.g., {"type": "json_object"})
                    **kwargs: Additional parameters passed to the API
                    
                Returns:
                    ChatCompletion object with the response
                """
                headers = {
                    'Authorization': f'Bearer {self.client.api_key}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Copilot-Integration-Id': 'copilot-chat'
                }
                
                data = {
                    'model': model,
                    'messages': messages,
                    'temperature': temperature,
                }
                
                if max_tokens is not None:
                    data['max_tokens'] = max_tokens
                
                # Handle response_format for JSON mode
                if response_format and response_format.get('type') == 'json_object':
                    # Add instruction to return JSON in the system message
                    # since Copilot API may not support response_format directly
                    pass  # The prompts already ask for JSON
                
                try:
                    response = requests.post(
                        self.client.API_ENDPOINT,
                        headers=headers,
                        json=data,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Parse the response into our objects
                        choices = []
                        for choice_data in result.get('choices', []):
                            message_data = choice_data.get('message', {})
                            message = Message(
                                content=message_data.get('content', ''),
                                role=message_data.get('role', 'assistant')
                            )
                            choice = Choice(
                                message=message,
                                finish_reason=choice_data.get('finish_reason', 'stop'),
                                index=choice_data.get('index', 0)
                            )
                            choices.append(choice)
                        
                        return ChatCompletion(
                            choices=choices,
                            model=result.get('model', model),
                            usage=result.get('usage', {})
                        )
                    
                    elif response.status_code == 401:
                        raise CopilotAPIError(
                            "Unauthorized: Check your GitHub PAT has Copilot access",
                            status_code=401,
                            response=response.text
                        )
                    
                    elif response.status_code == 400:
                        error_data = response.json() if response.text else {}
                        error_msg = error_data.get('error', response.text)
                        raise CopilotAPIError(
                            f"Bad Request: {error_msg}",
                            status_code=400,
                            response=response.text
                        )
                    
                    elif response.status_code == 429:
                        raise CopilotAPIError(
                            "Rate limited: Too many requests",
                            status_code=429,
                            response=response.text
                        )
                    
                    else:
                        raise CopilotAPIError(
                            f"API error: {response.status_code}",
                            status_code=response.status_code,
                            response=response.text
                        )
                        
                except requests.exceptions.Timeout:
                    raise CopilotAPIError("Request timed out")
                except requests.exceptions.ConnectionError:
                    raise CopilotAPIError("Connection error: Unable to reach Copilot API")
                except CopilotAPIError:
                    raise
                except Exception as e:
                    raise CopilotAPIError(f"Unexpected error: {str(e)}")


def test_api_key(api_key: str) -> Dict[str, Any]:
    """
    Test if a GitHub PAT is valid for the Copilot API.
    
    Args:
        api_key: GitHub Personal Access Token to test
        
    Returns:
        Dict with 'valid' boolean and 'message' or 'error' string
    """
    try:
        client = CopilotClient(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        return {'valid': True, 'message': 'GitHub PAT is valid for Copilot API!'}
    except CopilotAPIError as e:
        if e.status_code == 401:
            return {'valid': False, 'error': 'Invalid or unauthorized GitHub PAT'}
        elif e.status_code == 429:
            return {'valid': False, 'error': 'Rate limited - but token appears valid'}
        else:
            return {'valid': False, 'error': str(e.message)}
    except Exception as e:
        return {'valid': False, 'error': f'Connection error: {str(e)}'}
