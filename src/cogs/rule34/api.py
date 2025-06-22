import random
import requests
from cachetools import TTLCache
from dataclasses import dataclass
from typing import Final, List, Optional, Tuple


@dataclass
class Rule34Post:
    id: str
    tags: List[str]
    file_url: str

    @classmethod
    def from_dict(cls, post: dict) -> "Rule34Post":
        id_val = str(post.get("id", "unknown"))
        tags_raw = post.get("tags", "")
        file_url_val = str(post.get("file_url", ""))

        tags_list: List[str] = tags_raw.split() if isinstance(tags_raw, str) else []

        return cls(id=id_val, tags=tags_list, file_url=file_url_val)

    def get_output_string(self) -> str:
        tag_str = " ".join(self.tags)
        if len(tag_str) >= 1500:
            tag_str = tag_str[:1501] + "..."
        output = (
            f"`Post from https://rule34.xxx`\n\n"
            f"`ID` - `{self.id}`\n\n"
            f"`Tags` : `{tag_str}`\n\n"
            f"`URL` : {self.file_url}"
        )
        return output


@dataclass
class TagGroup:
    whitelisted: List[str]
    blacklisted: List[str]

    @classmethod
    def from_list(cls, whitelisted: List[str], blacklisted: List[str]) -> "TagGroup":
        whitelisted = [tag.replace("-", "") for tag in whitelisted]
        blacklisted = [tag.replace("-", "") for tag in blacklisted]

        return cls(whitelisted, blacklisted)

    @classmethod
    def from_string(cls, tags: str) -> "TagGroup":
        tag_list = tags.strip().lower().replace(",", " ").split(" ")
        tag_list = [tag for tag in tag_list if tag.strip()]

        blacklisted = sorted([tag[1:] for tag in tag_list if tag.startswith("-")])
        whitelisted = sorted([tag for tag in tag_list if not tag.startswith("-")])

        return cls(whitelisted, blacklisted)

    def to_string(self) -> str:
        all_tags = self.whitelisted + [f"-{tag}" for tag in self.blacklisted]
        return " ".join(all_tags)

    def append_to_whitelist(self, tags: List[str]) -> None:
        normalized = {
            tag.strip().lower().replace("-", "") for tag in tags if tag.strip()
        }
        self.whitelisted = sorted(set(self.whitelisted).union(normalized))

    def append_to_blacklist(self, tags: List[str]) -> None:
        normalized = {
            tag.strip().lower().replace("-", "") for tag in tags if tag.strip()
        }
        self.blacklisted = sorted(set(self.blacklisted).union(normalized))

    def get_conflicting_tags(self) -> List[str]:
        whitelist_set = set(self.whitelisted)
        blacklist_set = set(self.blacklisted)
        conflicts = whitelist_set.intersection(blacklist_set)
        return sorted(conflicts)


class Rule34API:
    API_URL: Final[str] = (
        "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1"
    )

    def __init__(self) -> None:
        # self.cache: Dict[str, List[Rule34Post]] = {}
        self.cache: TTLCache[str, List[Rule34Post]] = TTLCache(maxsize=1000, ttl=3600)

    def _retrieve_from_cache(self, key: str, pop: bool = True) -> Optional[Rule34Post]:
        posts = self.cache.get(key)
        if not posts:
            self.cache.pop(key, None)
            return None

        index = random.randint(0, len(posts) - 1)
        post = posts[index]

        if pop:
            posts.pop(index)

        return post

    def _push_to_cache(self, key: str, posts: List[Rule34Post]) -> None:
        self.cache[key] = posts

    def search(self, tags: TagGroup) -> Optional[Rule34Post]:
        query = tags.to_string()

        if self._retrieve_from_cache(query, False) is None:
            try:
                tag_query_string = query.replace(" ", "+")
                response = requests.get(
                    f"{self.API_URL}&tags={tag_query_string}&limit=1000"
                )
                response.raise_for_status()
                json_response = response.json()
            except (requests.RequestException, ValueError):
                return None

            posts: List[Rule34Post] = [
                Rule34Post.from_dict(post)
                for post in json_response
                if isinstance(post, dict)
            ]

            self._push_to_cache(query, posts)

        return self._retrieve_from_cache(query, True)

    def latest(self) -> Optional[Rule34Post]:
        try:
            response = requests.get(f"{self.API_URL}&limit=1")
            response.raise_for_status()
            json_data = response.json()
            post_data = (
                json_data[0] if json_data and isinstance(json_data[0], dict) else None
            )
            return Rule34Post.from_dict(post_data) if post_data else None
        except (requests.RequestException, ValueError, IndexError):
            return None
