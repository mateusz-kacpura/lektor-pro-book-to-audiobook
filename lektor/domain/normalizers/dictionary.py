"""
Technical dictionary of acronyms, terms, and abbreviations for Cloud Native and Go.
Maintains phonetic pronunciations for natural speech synthesis.
"""
import re

# Implementation note: see the surrounding code for the behavior described here.
ACRONYMS = {
    r"\bgRPC\b": "dĹĽi ar pi si",
    r"\bAPI\b": "ej pi aj",
    r"\bAPIs\b": "ej pi ajs",
    r"\bk8s\b": "Kubernetes",
    r"\bK8s\b": "Kubernetes",
    r"\bCI/CD\b": "ciÄ…gĹ‚a integracja i ciÄ…gĹ‚e wdraĹĽanie",
    r"\bCI\b": "si aj",
    r"\bCD\b": "si di",
    r"\bCSP\b": "ce es pe",
    r"\bHTTP\b": "ha te te pe",
    r"\bHTTPS\b": "ha te te pe es",
    r"\bTCP\b": "te ce pe",
    r"\bUDP\b": "u de pe",
    r"\bIP\b": "aj pi",
    r"\bJSON\b": "dĹĽejson",
    r"\bYAML\b": "jaml",
    r"\bXML\b": "iks em el",
    r"\bHTML\b": "ha te em el",
    r"\bCSS\b": "ce es es",
    r"\bSQL\b": "es kju el",
    r"\bNoSQL\b": "noĹ‚ es kju el",
    r"\bCLI\b": "ce el i",
    r"\bSDK\b": "es de ka",
    r"\bCPU\b": "ce pe u",
    r"\bRAM\b": "ram",
    r"\bGPU\b": "dĹĽi pi u",
    r"\bOS\b": "o es",
    r"\bUI\b": "ju aj",
    r"\bUX\b": "ju iks",
    r"\bSaaS\b": "sas",
    r"\bPaaS\b": "pas",
    r"\bIaaS\b": "jas",
    r"\bAWS\b": "a wu es",
    r"\bEC2\b": "i si tu",
    r"\bS3\b": "es trzy",
    r"\bEKS\b": "i kej es",
    r"\bGKE\b": "dĹĽi kej i",
    r"\bGCP\b": "dĹĽi si pi",
    r"\bURL\b": "u er el",
    r"\bURI\b": "ju ar aj",
    r"\bDNS\b": "de en es",
    r"\bTLS\b": "te el es",
    r"\bSSL\b": "es es el",
    r"\bRPC\b": "er pe ce",
    r"\bOOP\b": "o o pe",
    r"\bTTL\b": "te te el",
    r"\bQPS\b": "kju pi es",
    r"\bRPS\b": "er pi es",
    r"\bSLA\b": "es el a",
    r"\bSLO\b": "es el o",
    r"\bSLI\b": "es el i",
}

# Implementation note: see the surrounding code for the behavior described here.
POLISH_TECHNICAL_INFLECTIONS = {
    r"\bgoroutine\b": "gorutyna",
    r"\bgoroutines\b": "gorutyny",
    r"\bGoroutine\b": "Gorutyna",
    r"\bGoroutines\b": "Gorutyny",
    r"\bgoroutin\b": "gorutyn",
    r"\bmutex\b": "miuteks",
    r"\bmutexa\b": "miuteksa",
    r"\bmutexem\b": "miuteksem",
    r"\bmutexy\b": "miuteksy",
    r"\bmutexĂłw\b": "miuteksĂłw",
    r"\bhashmapa\b": "haszmapa",
    r"\bhashmapy\b": "haszmapy",
    r"\bhashmapie\b": "haszmapie",
}


def apply_pronunciation_rules(text: str) -> str:
    """Replaces technical abbreviations and acronyms with forms facilitating pronunciation."""
    if not text:
        return ""
        
    # Implementation note: see the surrounding code for the behavior described here.
    for pattern, replacement in ACRONYMS.items():
        text = re.sub(pattern, replacement, text)
        
    # Implementation note: see the surrounding code for the behavior described here.
    for pattern, replacement in POLISH_TECHNICAL_INFLECTIONS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
    return text
