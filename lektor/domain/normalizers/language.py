"""
Language detection and segment classification service ('pl' or 'en').
Pure domain logic without external ML dependencies.
"""
import re

POLISH_CHARS = set("Ä…Ä‡Ä™Ĺ‚Ĺ„ĂłĹ›ĹşĹĽÄ„Ä†ÄĹĹĂ“ĹšĹąĹ»")

# Implementation note: see the surrounding code for the behavior described here.
PURE_POLISH_WORDS = {
    "siÄ™", "jest", "jak", "ĹĽe", "dla", "przez", "ze", "za", "ale", "czy", "tym", 
    "jego", "jej", "oraz", "wiÄ™c", "bÄ™dzie", "moĹĽe", "tylko", "bardzo", "ktĂłry", 
    "ktĂłra", "ktĂłre", "ktĂłrych", "ktĂłrym", "jednak", "moĹĽna", "przed", "pod", "nad", 
    "jako", "rĂłwnieĹĽ", "takĹĽe", "czyli", "lub", "albo", "np", "itp", "itd", "tzn", 
    "tzw", "patrz", "zob", "roku", "lat", "strona", "strony", "rozdziaĹ‚", "rozdziaĹ‚u", 
    "rozdziaĹ‚y", "rysunek", "rysunku", "tabela", "tabeli", "przypis", "wydanie", 
    "autor", "autorzy", "wraz", "miÄ™dzy", "czasie", "sposĂłb", "wszystkie", "wszystkich",
    "wĹ‚asnych", "czÄ™Ĺ›ci", "koĹ„cowe", "pierwszy", "drugi", "trzeci", "jeden", "dwa", 
    "trzy", "sto", "tysiÄ…c", "wĹ‚aĹ›nie", "dobrze", "wiemy", "nazywamy", "czule", 
    "doprowadziÄ‡", "staje", "kaĹĽda", "nigdy", "bÄ™dÄ…", "byĹ‚by", "starannie", "prĂłby",
    "czynienia", "marnotrawstwem", "nieproduktywne", "wychodzÄ…c", "zaĹ‚oĹĽenia", "pewnoĹ›ciÄ…",
    "zawiodÄ…", "pozostaje", "sprawny", "wielu", "sposobĂłw", "wdraĹĽanie", "najczÄ™stszym",
    "podejĹ›ciem", "zakĹ‚ada", "dotknie", "bezpieczniki", "ponawiania", "prĂłb"
}

ENGLISH_WORDS = {
    "method", "methods", "type", "types", "receiver", "receivers", "struct", "structs", 
    "pointer", "pointers", "argument", "arguments", "parameter", "parameters", "field", "fields", 
    "slice", "slices", "map", "maps", "channel", "channels", "goroutine", "goroutines", 
    "concurrency", "parallelism", "mutex", "mutexes", "scope", "syntax", "keyword", "keywords", 
    "statement", "statements", "expression", "expressions", "literal", "literals", "nil", "panic", 
    "recover", "defer", "const", "var", "func", "function", "functions", "return", "returns", 
    "interface", "interfaces", "package", "packages", "module", "modules", "import", "imports", 
    "cloud", "native", "computing", "tier", "tiers", "presentation", "business", "data", 
    # Implementation note: see the surrounding code for the behavior described here.
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", 
    "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his", 
    "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my", 
    "one", "all", "would", "there", "their", "what", "so", "up", "out", "if", 
    "about", "who", "get", "which", "go", "me", "when", "make", "can", "like", 
    "time", "no", "just", "him", "know", "take", "people", "into", "year", "your", 
    "good", "some", "could", "them", "see", "other", "than", "then", "now", "look", 
    "only", "come", "its", "over", "think", "also", "back", "after", "use", "two", 
    "how", "our", "work", "first", "well", "way", "even", "new", "want", "because",
    "any", "these", "give", "day", "most", "us", "why", "wrote", "written", "write", 
    "book", "books", "chapter", "chapters", "page", "pages", "conventions", "used", 
    "praise", "acknowledgments", "acknowledgment", "appendix", "index", "turtles", "down",
    
    # Implementation note: see the surrounding code for the behavior described here.
    "fault", "faults", "bug", "bugs", "error", "errors", "failure", "failures", 
    "crash", "crashes", "total", "partial", "system", "systems", "subsystem", "subsystems", 
    "component", "components", "architecture", "architectures", "multitiered", "tier", "tiers", 
    "presentation", "business", "logic", "data", "terminal", "terminals", "dumb", "smart", 
    "client", "server", "cloud", "native", "computing", "microservice", "microservices", 
    "distributed", "monolith", "monolithic", "container", "containers", "docker", "kubernetes", 
    "k8s", "pod", "pods", "node", "nodes", "cluster", "clusters", "service", "services", 
    "mesh", "gateway", "ingress", "egress", "proxy", "load", "balancer", "balancing", 
    "shedding", "circuit", "breaker", "breakers", "retry", "retries", "exponential", 
    "backoff", "jitter", "timeout", "timeouts", "deadline", "deadlines", "cancellation", 
    "context", "health", "check", "checks", "probe", "probes", "liveness", "readiness", 
    "metric", "metrics", "telemetry", "trace", "traces", "tracing", "span", "spans", 
    "log", "logs", "logging", "observable", "observability", "monitoring", "alert", 
    "alerts", "alerting", "disaster", "recovery", "failover", "backup", "redundancy", 
    "redundant", "replica", "replicas", "state", "stateless", "stateful", "cache", 
    "caching", "redis", "database", "databases", "storage", "queue", "queues", 
    "message", "broker", "stream", "streaming", "kafka", "payload", "throughput", 
    "latency", "bandwidth", "overhead", "bottleneck", "benchmark", "profiling", 
    "goroutine", "goroutines", "channel", "channels", "mutex", "mutexes", "lock", 
    "locks", "deadlock", "deadlocks", "race", "condition", "thread", "threads", 
    "concurrency", "concurrent", "parallel", "worker", "pool", "pipeline", "pipelines", 
    "workflow", "deploy", "deployment", "release", "canary", "infrastructure", "iac", 
    "terraform", "gitops", "devops", "sre", "site", "reliability", "engineer", 
    "engineering", "engineers", "senior", "lead", "staff", "principal", "architect", 
    "developer", "developers", "programmer", "programmers", "author", "edition", 
    "preface", "foreword", "summary", "pattern", "patterns", "trade-off", "trade-offs", 
    "best", "practices", "convention", "italic", "bold", "constant", "width", 
    "runtime", "framework", "library", "interface", "struct", "function", "variable", 
    "pointer", "slice", "array", "map", "string", "package", "loose", "coupling", 
    "loosely", "coupled", "scale", "scalable", "scalability", "resilient", "resilience",
    "manageable", "manageability", "upstream", "downstream", "dependency", "dependencies"
}

ENGLISH_SUFFIXES = (
    "tion", "tions", "sion", "sions", "ment", "ments", "able", "ables", "ible", "ibles", 
    "ing", "ings", "ity", "ities", "ive", "ives", "ous", "ance", "ances", "ence", "ences", 
    "less", "ness", "nesses", "ward", "wards", "wise", "ize", "izes", "ized", "izing", 
    "ise", "ises", "ised", "ising", "er", "ers", "or", "ors", "ist", "ists", "ism", "isms", 
    "ic", "ics", "ical", "ful", "fully", "ly", "ed"
)


def is_english_phrase(text: str) -> bool:
    """Checks whether phrase should be read with native English accent (lang='en')."""
    clean = text.strip()
    # Implementation note: see the surrounding code for the behavior described here.
    clean = re.sub(r"^(?:ang\.?|angielski:?|ang:?)\s*", "", clean, flags=re.IGNORECASE)
    clean = clean.strip("\"'()[]{}")
    
    # 1. Polish diacritics -> 100% Polish
    if any(c in POLISH_CHARS for c in clean):
        return False
        
    words = [w.lower() for w in re.findall(r"\b[a-zA-Z']+\b", clean)]
    if not words:
        return False
        
    # Implementation note: see the surrounding code for the behavior described here.
    if any(w in PURE_POLISH_WORDS for w in words):
        return False
        
    # Implementation note: see the surrounding code for the behavior described here.
    en_word_count = sum(1 for w in words if w in ENGLISH_WORDS)
    en_suffix_count = sum(1 for w in words if any(w.endswith(sfx) for sfx in ENGLISH_SUFFIXES))
    
    if en_word_count > 0 or en_suffix_count > 0:
        return True

    return False


def detect_language(text: str, default_lang: str = "pl") -> str:
    """Classifies a text segment as 'pl' (Polish) or 'en' (English)."""
    clean_text = text.strip()
    if not clean_text:
        return default_lang
        
    # Implementation note: see the surrounding code for the behavior described here.
    if any(c in POLISH_CHARS for c in clean_text):
        return "pl"
        
    # Implementation note: see the surrounding code for the behavior described here.
    if is_english_phrase(clean_text):
        return "en"
        
    words = [w.lower() for w in re.findall(r"\b[a-zA-Z']+\b", clean_text)]
    if not words:
        return default_lang
        
    pl_score = sum(1 for w in words if w in PURE_POLISH_WORDS)
    en_score = sum(1 for w in words if w in ENGLISH_WORDS)

    if pl_score > 0:
        return "pl"
    elif en_score > 0:
        return "en"

    return default_lang

