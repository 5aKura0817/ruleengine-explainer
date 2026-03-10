from typing import Any, Dict

import requests

from ruleengine.config import API_BASE_URL, NCS_USER_TOKEN, TEAMID


class APIClient:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.headers = {
            'Teamid': TEAMID,
            'Cookie': f'ncs-user-token={NCS_USER_TOKEN}'
        }

    def get_rule_list(self, page_num: int = 1, page_size: int = 50, enabled_only: bool = False) -> Dict[str, Any]:
        """Fetch paginated rule list

        Args:
            enabled_only: When True, passes disabled=false to filter server-side
        """
        url = f"{self.base_url}/admin/rule/page"
        params = {
            'pageNum': page_num,
            'pageSize': page_size
        }
        if enabled_only:
            params['disabled'] = 'false'
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_rule_detail(self, rule_id: int) -> Dict[str, Any]:
        """Fetch detailed rule configuration"""
        url = f"{self.base_url}/admin/rule/{rule_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
