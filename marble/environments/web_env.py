import time
from typing import Any, Dict, Union

import requests

from marble.agent import ReasoningAgent
from marble.environments.base_env import BaseEnvironment

AgentType = Union[ReasoningAgent]  # Will expand to include other agent types

class WebEnvironment(BaseEnvironment):
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the WebEnvironment.

        Args:
            name (str): The name of the environment.
        """
        super().__init__(name, config)
        self.last_visited_timestamp: float = 0
        self.last_visited_url: str = ""
        self.web_cache: Dict[str, str] = {}  # Cache for storing webpage content

        # Register the fetch_webpage action
        self.register_action("fetch_webpage", self._fetch_webpage_handler)

    def _fetch_webpage_handler(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Action handler to fetch a webpage.

        Args:
            params (Dict[str, Any]): Parameters for the action, including the 'url'.

        Returns:
            Dict[str, Any]: The result of the action, including the webpage content.
        """
        url = params.get('url')
        if not url:
            return {
                "success": False,
                "error-msg": "URL is required to fetch a webpage."
            }

        # Check if the URL is already cached
        if url in self.web_cache:
            content = self.web_cache[url]
        else:
            # Set up a browser-like User-Agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.0.0'
            }

            while time.time() - self.last_visited_timestamp < 1:
                time.sleep(0.5)

            try:
                response = requests.get(url, headers=headers, timeout=5.0)  # 5 second timeout
                response.raise_for_status()  # Raise an error for bad responses
                content = response.text
                self.web_cache[url] = content
                self.last_visited_url = url
                self.last_visited_timestamp = time.time()
            except requests.RequestException as e:
                return {
                    "success": False,
                    "error-msg": str(e)
                }

        return {
            "success": True,
            "error-msg": ""
        }


    def get_state(self) -> Dict[str, Any]:
        """
        Get the current environment state.

        Returns:
            Dict[str, Any]: The current environment state.
        """
        return {
            "url": self.last_visited_url,
            "content": self.web_cache[self.last_visited_url] if self.last_visited_url else ""
        }