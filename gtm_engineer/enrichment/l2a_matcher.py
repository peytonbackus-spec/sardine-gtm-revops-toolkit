import re
from typing import List, Optional, Set, Tuple

from pydantic import BaseModel, Field

FREE_EMAIL_PROVIDERS: Set[str] = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
    "aol.com", "protonmail.com", "zoho.com", "mail.com", "gmx.com"
}

LEGAL_SUFFIXES: Set[str] = {
    "inc", "incorporated", "llc", "limited liability company", "corp",
    "corporation", "ltd", "limited", "co", "company", "plc", "gmbh",
    "sa", "sas", "bv", "pvt", "pte", "group", "technologies", "tech",
    "solutions", "services", "holdings", "global", "international"
}

def normalize_domain(raw_domain_or_email: str) -> Optional[str]:
    if not raw_domain_or_email:
        return None
    val = raw_domain_or_email.strip().lower()
    if "@" in val:
        val = val.split("@")[-1]
    val = re.sub(r"^https?://", "", val)
    val = val.split("/")[0].split(":")[0]
    if val in FREE_EMAIL_PROVIDERS:
        return None
    parts = val.split(".")
    if len(parts) > 2 and parts[0] in {"www", "app", "mail", "blog", "go", "info"}:
        val = ".".join(parts[1:])
    return val if "." in val else None

def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    clean = re.sub(r"[^\w\s]", "", name.lower().strip())
    words = clean.split()
    filtered = [w for w in words if w not in LEGAL_SUFFIXES]
    return " ".join(filtered) if filtered else clean

def jaro_winkler_similarity(s1: str, s2: str, p: float = 0.1, max_l: int = 4) -> float:
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    max_dist = max(len1, len2) // 2 - 1
    if max_dist < 0:
        max_dist = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - max_dist)
        end = min(i + max_dist + 1, len2)
        for j in range(start, end):
            if s2_matches[j]:
                continue
            if s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    transpositions = transpositions // 2
    jaro = ((matches / len1) + (matches / len2) + ((matches - transpositions) / matches)) / 3.0

    prefix_len = 0
    for i in range(min(len1, len2, max_l)):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break

    return jaro + (prefix_len * p * (1 - jaro))

class AccountRecord(BaseModel):
    id: str
    name: str
    primary_domain: str
    secondary_domains: List[str] = Field(default_factory=list)

class LeadRecord(BaseModel):
    id: str
    email: str
    company_name: Optional[str] = None
    website: Optional[str] = None

class MatchResult(BaseModel):
    lead_id: str
    account_id: Optional[str] = None
    confidence_score: float
    match_strategy: str
    matched_by_value: Optional[str] = None

class LeadToAccountMatcher:
    def __init__(self, fuzzy_threshold: float = 0.88, review_threshold: float = 0.75):
        self.fuzzy_threshold = fuzzy_threshold
        self.review_threshold = review_threshold

    def find_match(self, lead: LeadRecord, target_accounts: List[AccountRecord]) -> MatchResult:
        lead_domain = normalize_domain(lead.email) or (normalize_domain(lead.website) if lead.website else None)
        lead_name_clean = normalize_company_name(lead.company_name) if lead.company_name else ""

        if lead_domain:
            for acc in target_accounts:
                acc_domains = [normalize_domain(acc.primary_domain)] + [normalize_domain(d) for d in acc.secondary_domains]
                if lead_domain in filter(None, acc_domains):
                    return MatchResult(
                        lead_id=lead.id,
                        account_id=acc.id,
                        confidence_score=1.0,
                        match_strategy="exact_domain",
                        matched_by_value=lead_domain
                    )

        if lead_name_clean:
            for acc in target_accounts:
                acc_name_clean = normalize_company_name(acc.name)
                if lead_name_clean == acc_name_clean:
                    return MatchResult(
                        lead_id=lead.id,
                        account_id=acc.id,
                        confidence_score=0.98,
                        match_strategy="exact_normalized_name",
                        matched_by_value=lead_name_clean
                    )

        best_match: Optional[Tuple[AccountRecord, float]] = None
        if lead_name_clean:
            for acc in target_accounts:
                acc_name_clean = normalize_company_name(acc.name)
                score = jaro_winkler_similarity(lead_name_clean, acc_name_clean)
                if best_match is None or score > best_match[1]:
                    best_match = (acc, score)

        if best_match and best_match[1] >= self.fuzzy_threshold:
            return MatchResult(
                lead_id=lead.id,
                account_id=best_match[0].id,
                confidence_score=round(best_match[1], 4),
                match_strategy="fuzzy_jaro_winkler",
                matched_by_value=best_match[0].name
            )

        if best_match and best_match[1] >= self.review_threshold:
            return MatchResult(
                lead_id=lead.id,
                account_id=best_match[0].id,
                confidence_score=round(best_match[1], 4),
                match_strategy="flagged_manual_review",
                matched_by_value=best_match[0].name
            )

        return MatchResult(
            lead_id=lead.id,
            account_id=None,
            confidence_score=0.0,
            match_strategy="unmatched",
            matched_by_value=None
        )
