from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TagGroup:
    whitelisted: List[str] = field(default_factory=list)
    blacklisted: List[str] = field(default_factory=list)
    additional_key: Optional[str] = None

    @staticmethod
    def _normalize_tag(tag: str) -> str:
        return tag.strip().lower().replace("-", "")

    @classmethod
    def from_list(
        cls,
        whitelisted: List[str],
        blacklisted: List[str],
        additional_key: Optional[str] = None,
    ) -> "TagGroup":
        whitelisted = [cls._normalize_tag(tag) for tag in whitelisted]
        blacklisted = [cls._normalize_tag(tag) for tag in blacklisted]
        return cls(whitelisted, blacklisted, additional_key)

    @classmethod
    def from_string(cls, tags: str, additional_key: Optional[str] = None) -> "TagGroup":
        if not tags or not tags.strip():
            return cls()

        normalized_tags = tags.strip().lower().replace(",", " ")
        tag_list = [tag.strip() for tag in normalized_tags.split() if tag.strip()]

        blacklisted = sorted([tag[1:] for tag in tag_list if tag.startswith("-")])
        whitelisted = sorted([tag for tag in tag_list if not tag.startswith("-")])

        return cls(whitelisted, blacklisted, additional_key)

    def to_string(self) -> str:
        all_tags = self.whitelisted + [f"-{tag}" for tag in self.blacklisted]
        return " ".join(all_tags)

    def to_key(self) -> str:
        additional_key = ""
        if (key := self.additional_key) is not None:
            additional_key = f"[[{key}]]"

        return self.to_string() + additional_key

    def append_to_whitelist(self, tags: List[str]) -> None:
        if not tags:
            return

        normalized = {self._normalize_tag(tag) for tag in tags if tag.strip()}
        self.whitelisted = sorted(set(self.whitelisted).union(normalized))

    def append_to_blacklist(self, tags: List[str]) -> None:
        if not tags:
            return

        normalized = {self._normalize_tag(tag) for tag in tags if tag.strip()}
        self.blacklisted = sorted(set(self.blacklisted).union(normalized))

    def get_conflicting_tags(self) -> List[str]:
        whitelist_set = set(self.whitelisted)
        blacklist_set = set(self.blacklisted)
        return sorted(whitelist_set.intersection(blacklist_set))

    def is_valid(self) -> bool:
        return len(self.get_conflicting_tags()) == 0

    def resolve_conflicts(self, prefer_whitelist: bool = True) -> None:
        conflicts = self.get_conflicting_tags()
        if not conflicts:
            return

        if prefer_whitelist:
            self.blacklisted = [tag for tag in self.blacklisted if tag not in conflicts]
        else:
            self.whitelisted = [tag for tag in self.whitelisted if tag not in conflicts]
