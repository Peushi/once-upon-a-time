import requests
from django.conf import settings


class FlaskAPIClient:
    def __init__(self):
        self.url = settings.FLASK_API_URL
        self.key = settings.FLASK_API_KEY

    def _get_head(self, include_auth=False):
        headers = {"Content-Type": "application/json"}
        if include_auth:
            headers["X-API-KEY"] = self.key
        return headers

    def _handle_response(self, response):
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            try:
                error_data = response.json()
                raise Exception(
                    f"API Error: {error_data.get('error', 'Unknown error')}"
                )
            except:
                raise Exception(f"API Error: HTTP {response.status_code}")
        return response.json()

    # read endpoints

    def get_stories(self, status=None, search=None, tags=None):
        params = {}
        if status:
            params["status"] = status
        if search:
            params["search"] = search
        if tags:
            params["tags"] = tags

        try:
            response = requests.get(
                f"{self.url}/stories", params=params, timeout=10
            )  # ------------------------------
            data = self._handle_response(response)
            return data if data else []
        except Exception as e:
            print(f"Error fetching stories: {e}")
            return []

    def get_story(self, story_id, include_pages=False):
        try:
            params = {"include_pages": "true"} if include_pages else {}
            response = requests.get(
                f"{self.url}/stories/{story_id}", params=params, timeout=10
            )
            return self._handle_response(response)
        except Exception as e:
            print(f"Error fetching story {story_id}: {e}")
            return None

    def get_story_start(self, story_id):
        try:
            response = requests.get(f"{self.url}/stories/{story_id}/start", timeout=10)
            data = self._handle_response(response)
            if not data:
                return None
            return data
        except Exception as e:
            print(f"Error fecthing start of story {story_id}: {e}")
            return None

    def get_page(self, page_id):
        try:
            response = requests.get(f"{self.url}/pages/{page_id}", timeout=10)
            return self._handle_response(response)
        except Exception as e:
            print(f"Error fecthing page {page_id}: {e}")
            return None

    def get_story_tree(self, story_id: int):

        try:
            response = requests.get(
                f"{self.base_url}/stories/{story_id}/tree",
                timeout=10
            )
            return self._handle_response(response)
        except Exception as e:
            print(f"Error fetching story tree {story_id}: {e}")
            return None

    # writing endpoints

    def create_story(
        self, title, description="", status="draft", author_id=None, tags=None
    ):
        try:
            data = {
                "title": title,
                "description": description,
                "status": status,
                "author_id": author_id,
                "tags": tags if tags else [],
            }
            response = requests.post(
                f"{self.url}/stories",
                json=data,
                headers=self._get_head(include_auth=True),
                timeout=10,
            )
            result = self._handle_response(response)
            if not result:
                return None

            # Flask may return {"story": {...}} or just {...}
            if isinstance(result, dict) and "story" in result:
                return result["story"]
            return result

        except Exception as e:
            print(f"Error creating story: {e}")
            return None

    def update_story(self, story_id, **kwargs):
        try:
            response = requests.put(
                f"{self.url}/stories/{story_id}",
                json=kwargs,
                headers=self._get_head(include_auth=True),
                timeout=10,
            )
            result = self._handle_response(response)
            if not result:
                return None
            if isinstance(result, dict) and "story" in result:
                return result["story"]
            return result

        except Exception as e:
            print(f"Error updating story {story_id} : {e}")
            return None

    def delete_story(self, story_id):
        try:
            response = requests.delete(
                f"{self.url}/stories/{story_id}",
                headers=self._get_head(include_auth=True),
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error deleteing story {story_id}: {e}")
            return False

    def create_page(self, story_id, text, is_ending=False, ending_label=None):
        try:
            data = {
                "text": text,
                "is_ending": is_ending,
                "ending_label": ending_label,
            }

            response = requests.post(
                f"{self.url}/stories/{story_id}/pages",
                json=data,
                headers=self._get_head(include_auth=True),
                timeout=10,
            )
            result = self._handle_response(response)
            if not result:
                return None
            # Flask returns {"page": {...}} (not "pages")
            if isinstance(result, dict) and "page" in result:
                return result["page"]
            return result

        except Exception as e:
            print(f"Error creating page: {e}")
            return None

    def update_page(self, page_id, **kwargs):
        try:
            response = requests.put(
                f"{self.url}/pages/{page_id}",
                json=kwargs,
                headers=self._get_head(include_auth=True),
                timeout=10,
            )
            result = self._handle_response(response)
            return result if result else None
        except Exception as e:
            print(f"Error updating page {page_id} : {e}")
            return None

    def delete_page(self, page_id):
        try:
            response = requests.delete(
                f"{self.url}/pages/{page_id}",
                headers=self._get_head(include_auth=True),
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error deleteing page {page_id}: {e}")
            return False

    def create_choice(self, page_id, text, next_page_id):
        try:
            data = {
                "text": text,
                "next_page_id": next_page_id,
            }

            response = requests.post(
                f"{self.url}/pages/{page_id}/choices",
                json=data,
                headers=self._get_head(include_auth=True),
                timeout=10,
            )
            result = self._handle_response(response)
            if not result:
                return None

            # Flask may return {"choice": {...}} or just {...}
            if isinstance(result, dict) and "choice" in result:
                return result["choice"]
            return result

        except Exception as e:
            print(f"Error creating choice: {e}")
            return None

    def update_choice(self, choice_id, **kwargs):
        try:
            response = requests.put(
                f"{self.url}/choices/{choice_id}",
                json=kwargs,
                headers=self._get_head(include_auth=True),
                timeout=10,
            )
            result = self._handle_response(response)
            return result if result else None
        except Exception as e:
            print(f"Error updating choice {choice_id} : {e}")
            return None

    def delete_choice(self, choice_id):
        try:
            response = requests.delete(
                f"{self.url}/choices/{choice_id}",
                headers=self._get_head(include_auth=True),
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error deleteing choice {choice_id}: {e}")
            return False


flask_api = FlaskAPIClient()
