from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RelevantResult:
    url: str
    title: str
    summary: str
    match_score: float
    relevance_score: float
    search_term: str
    engine: str
    timestamp: datetime


@dataclass
class FailedScrape:
    url: str
    label: str  # "timeout" or "anti-bot"
    search_term: str
    engine: str
    timestamp: datetime


@dataclass
class TechnicalError:
    url: str
    category: str  # http_error, ssl_error, dns_error, etc.
    description: str
    search_term: str
    engine: str
    timestamp: datetime
