from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class NoResult:
    type: str
    value: str

@dataclass
class ResultMatcher:
    type: str
    value: str

@dataclass
class FieldExtraction:
    type: str
    value: str
    multiple: bool = False

@dataclass
class Extraction:
    recordsSelector: str
    fields: Dict[str, FieldExtraction]

@dataclass
class Pagination:
    type: str
    paramName: str
    start: int
    maxPages: int

@dataclass
class Legal:
    allowed: Optional[bool] = None
    note: Optional[str] = None

@dataclass
class Site:
    id: str
    name: str
    homeUrl: str
    urlTemplate: str
    placeholders: List[str]
    urlEncode: bool
    method: str
    responseType: str
    requiresJs: bool
    noResult: NoResult
    headers: Dict[str, str] = field(default_factory=dict)
    resultMatcher: Optional[ResultMatcher] = None
    extract: Optional[Extraction] = None
    pagination: Optional[Pagination] = None
    rateLimitPerMinute: Optional[int] = None
    timeoutSeconds: Optional[int] = None
    retries: Optional[int] = None
    lastVerified: Optional[str] = None
    active: bool = True
    legal: Optional[Legal] = None
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    advanced_placeholders: List[str] = field(default_factory=list)

@dataclass
class CountrySites:
    country: str
    sites: List[Site]
    country_code: Optional[str] = None