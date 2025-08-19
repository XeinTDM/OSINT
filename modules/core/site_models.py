from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class NoResult(BaseModel):
    type: str
    value: str

class ResultMatcher(BaseModel):
    type: str
    value: str

class FieldExtraction(BaseModel):
    type: str
    value: str
    multiple: bool = False

class Extraction(BaseModel):
    recordsSelector: str
    fields: Dict[str, FieldExtraction]

class Pagination(BaseModel):
    type: str
    paramName: str
    start: int
    maxPages: int

class Legal(BaseModel):
    allowed: Optional[bool] = None
    note: Optional[str] = None

class Site(BaseModel):
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
    headers: Dict[str, str] = Field(default_factory=dict)
    resultMatcher: Optional[ResultMatcher] = None
    extract: Optional[Extraction] = None
    pagination: Optional[Pagination] = None
    rateLimitPerMinute: Optional[int] = None
    timeoutSeconds: Optional[int] = None
    retries: Optional[int] = None
    lastVerified: Optional[str] = None
    active: bool = True
    legal: Optional[Legal] = None
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    advanced_placeholders: List[str] = Field(default_factory=list)

class CountrySites(BaseModel):
    country: str
    sites: List[Site]
    country_code: Optional[str] = None