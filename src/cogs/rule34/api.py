import random
import requests
from cachetools import TTLCache
from dataclasses import dataclass
from typing import Any, Dict, Final, List, Optional
from urllib.parse import quote_plus

from cogs.rule34.tag_group import TagGroup


@dataclass
class Rule34Post:
    id: str
    tags: List[str]
    file_url: str

    @classmethod
    def from_dict(cls, post: Dict[str, Any]) -> "Rule34Post":
        id_val = str(post.get("id", "unknown"))
        tags_raw = post.get("tags", "")
        file_url_val = str(post.get("file_url", ""))

        tags_list: List[str] = tags_raw.split() if isinstance(tags_raw, str) else []

        return cls(id=id_val, tags=tags_list, file_url=file_url_val)

    def get_output_string(self, max_tag_length: int = 1500) -> str:
        tag_str = " ".join(self.tags)
        if len(tag_str) >= max_tag_length:
            tag_str = tag_str[: max_tag_length - 3] + "..."

        output = (
            f"`Post from https://rule34.xxx`\n\n"
            f"`ID`: `{self.id}`\n\n"
            f"`Tags`: `{tag_str}`\n\n"
            f"`URL`: {self.file_url}"
        )
        return output

    def __post_init__(self):
        if not self.id:
            raise ValueError("Post ID cannot be empty")
        if not self.file_url:
            raise ValueError("Post file URL cannot be empty")


class Rule34APIError(Exception):
    pass


class Rule34API:
    API_URL: Final[str] = (
        "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1"
    )
    DEFAULT_LIMIT: Final[int] = 1000
    DEFAULT_TIMEOUT: Final[int] = 30

    def __init__(
        self,
        cache_size: int = 1000,
        cache_ttl: int = 3600,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.cache: TTLCache[str, List[Rule34Post]] = TTLCache(
            maxsize=cache_size, ttl=cache_ttl
        )
        self.timeout = timeout
        self.session = requests.Session()

    def _retrieve_from_cache(self, key: str, pop: bool = True) -> Optional[Rule34Post]:
        posts = self.cache.get(key)
        if not posts:
            self.cache.pop(key, None)
            return None

        index = random.randint(0, len(posts) - 1)
        post = posts[index]

        if pop:
            posts.pop(index)

            if not posts:
                self.cache.pop(key, None)

        return post

    def _push_to_cache(self, key: str, posts: List[Rule34Post]) -> None:
        if posts:
            self.cache[key] = posts

    def _make_request(self, url: str) -> List[Any]:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise Rule34APIError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise Rule34APIError("Connection error occurred")
        except requests.exceptions.HTTPError as e:
            raise Rule34APIError(f"HTTP error: {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            raise Rule34APIError(f"Request failed: {str(e)}")
        except ValueError as e:
            raise Rule34APIError(f"Invalid JSON response: {str(e)}")

    def search(
        self, tags: TagGroup, limit: int = DEFAULT_LIMIT, prefer_whitelist: bool = True
    ) -> Optional[Rule34Post]:
        if not tags.is_valid():
            tags.resolve_conflicts(prefer_whitelist)

        query = tags.to_string()
        key = tags.to_key()

        cached_post = self._retrieve_from_cache(key, False)
        if cached_post is None:
            try:
                tag_query_string = quote_plus(query)
                url = f"{self.API_URL}&tags={tag_query_string}&limit={limit}"

                json_response = self._make_request(url)

                if not isinstance(json_response, list):
                    return None

                posts: List[Rule34Post] = []
                for post_data in json_response:
                    try:
                        if not isinstance(post_data, dict):
                            raise TypeError

                        post = Rule34Post.from_dict(post_data)
                        posts.append(post)
                    except (ValueError, TypeError) as e:
                        continue

                if not posts:
                    return None

                self._push_to_cache(key, posts)
            except Rule34APIError as e:
                return None

        return self._retrieve_from_cache(key, True)

    def latest(self) -> Optional[Rule34Post]:
        try:
            url = f"{self.API_URL}&limit=1"
            json_data = self._make_request(url)

            if not isinstance(json_data, list):
                return None

            post_data: Dict[str, Any] = json_data[0]
            return Rule34Post.from_dict(post_data)
        except (Rule34APIError, ValueError, IndexError) as e:
            return None
