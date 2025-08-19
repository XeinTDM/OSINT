from typing import Optional, List, Dict, Union, Any
from urllib.parse import urlparse
from pydantic import BaseModel, Field, ConfigDict, model_validator
import random

from modules.enums import HttpMethod, ResponseType, CheckMethods, ErrorTypes, CheckTypes

class NoResult(BaseModel):
    model_config = ConfigDict(extra='ignore')
    type: str
    value: str

class ResultMatcher(BaseModel):
    model_config = ConfigDict(extra='ignore')
    type: Optional[str] = None
    value: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _handle_empty_result_matcher(cls, data):
        """Handle empty resultMatcher objects {} by returning None."""
        if isinstance(data, dict) and not data:
            return None
        return data

class FieldExtraction(BaseModel):
    model_config = ConfigDict(extra='ignore')
    type: str
    value: str
    multiple: bool = False

class Extraction(BaseModel):
    model_config = ConfigDict(extra='ignore')
    recordsSelector: Optional[str] = None
    fields: Optional[Dict[str, FieldExtraction]] = None

class Pagination(BaseModel):
    model_config = ConfigDict(extra='ignore')
    type: Optional[str] = None
    paramName: Optional[str] = None
    start: Optional[int] = None
    maxPages: Optional[int] = None

class Legal(BaseModel):
    model_config = ConfigDict(extra='ignore')
    allowed: Optional[bool] = None
    note: Optional[str] = None

class Site(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: str
    name: str
    urlTemplate: str
    homeUrl: Optional[str] = None
    placeholders: List[str] = Field(default_factory=list)
    urlEncode: bool = False
    method: str = HttpMethod.GET.value
    responseType: str = ResponseType.HTML.value
    requiresJs: bool = False
    checkMethod: CheckMethods = Field(default=CheckMethods.BASIC)
    errorType: ErrorTypes = Field(default=ErrorTypes.STATUS_CODE)
    checkType: CheckTypes = Field(default=CheckTypes.NEGATIVE)
    errorString: Optional[Union[str, List[str]]] = None
    successString: Optional[str] = None
    noResult: Optional[Union[NoResult, List[NoResult]]] = None
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
    # New field for custom URL generation
    urlGenerator: Optional[str] = None
    # New field for custom check methods
    customCheck: Optional[str] = None

    def generate_url(self, username: str) -> str:
        """
        Generate the final URL for a site, handling advanced patterns.
        """
        if self.urlGenerator:
            return self._generate_custom_url(username)
        else:
            # Handle legacy {} placeholders for backward compatibility
            if '{}' in self.urlTemplate:
                return self.urlTemplate.format(username)
            else:
                return self.urlTemplate.format(username=username)
    
    def _generate_custom_url(self, username: str) -> str:
        """
        Handle custom URL generation patterns.
        """
        # Since we removed Stack Overflow and Roblox, this is no longer needed
        # but keeping for potential future use
        return self.urlTemplate.format(username=username)

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_username_schema(cls, data):
        """
        Allow legacy username site entries that use keys like 'url', lack 'id', 'homeUrl', etc.
        - Map 'url' -> 'urlTemplate'
        - Infer 'homeUrl' from URL
        - Generate 'id' from name if missing
        - Provide default placeholders based on url template
        - Derive 'requiresJs' from 'checkMethod' if not provided
        - Normalize enums provided as lowercase strings is handled by pydantic
        """
        if not isinstance(data, dict):
            return data

        site = dict(data)

        # url -> urlTemplate
        if 'urlTemplate' not in site and 'url' in site and isinstance(site['url'], str):
            site['urlTemplate'] = site['url']

        # Infer homeUrl
        if 'homeUrl' not in site and 'urlTemplate' in site and isinstance(site['urlTemplate'], str):
            try:
                parsed = urlparse(site['urlTemplate'])
                if parsed.scheme and parsed.netloc:
                    site['homeUrl'] = f"{parsed.scheme}://{parsed.netloc}"
            except Exception:
                pass

        if 'id' not in site and 'name' in site and isinstance(site['name'], str):
            slug = ''.join(ch.lower() if ch.isalnum() else '_' for ch in site['name']).strip('_')
            site['id'] = f"{slug}_legacy"

        if 'placeholders' not in site and 'urlTemplate' in site and isinstance(site['urlTemplate'], str):
            template: str = site['urlTemplate']
            if '{}' in template:
                site['placeholders'] = ['username']
            else:
                names: List[str] = []
                current = ''
                in_braces = False
                for ch in template:
                    if ch == '{':
                        in_braces = True
                        current = ''
                    elif ch == '}':
                        if in_braces and current:
                            names.append(current)
                        in_braces = False
                    elif in_braces:
                        current += ch
                site['placeholders'] = names or ['username']

        if 'requiresJs' not in site and 'checkMethod' in site:
            try:
                requires = str(site['checkMethod']).lower() == CheckMethods.DYNAMIC.value
                site['requiresJs'] = requires
            except Exception:
                pass

        if 'urlEncode' not in site:
            site['urlEncode'] = False

        if 'method' not in site:
            site['method'] = HttpMethod.GET.value
        if 'responseType' not in site:
            site['responseType'] = ResponseType.HTML.value

        if 'resultMatcher' in site and isinstance(site['resultMatcher'], dict) and not site['resultMatcher']:
            site['resultMatcher'] = None

        return site

class CountrySites(BaseModel):
    model_config = ConfigDict(extra='ignore')
    country: str
    sites: List[Site]
    country_code: Optional[str] = None