"""
Configuration for guidelines tool.

Contains curated research guidance sources from leading researchers
and institutions for evidence-based academic mentoring.
"""

from __future__ import annotations

from typing import Dict, List
import os
from urllib.parse import urlparse


class GuidelinesConfig:
    """Configuration for research guidelines sources and search parameters."""
    
    # Cost Optimization Settings
    ENABLE_CACHING = True
    CACHE_TTL_HOURS = 24  # Cache responses for 24 hours
    MAX_SEARCH_QUERIES = 3  # Limit to 3 queries to control costs
    ENABLE_COST_MONITORING = True

    # Feature flag to enable v2 structured evidence API (default ON)
    FF_GUIDELINES_V2 = os.getenv("FF_GUIDELINES_V2", "1").strip().lower() in {"1", "true", "yes", "on"}

    # V2 defaults/caps
    DEFAULT_MAX_PER_SOURCE = int(os.getenv("GUIDELINES_MAX_PER_SOURCE", "3"))
    RESULT_CAP = int(os.getenv("GUIDELINES_RESULT_CAP", "30"))
    DEFAULT_MODE = os.getenv("GUIDELINES_DEFAULT_MODE", "fast").lower()  # fast|exhaustive
    RESPONSE_FORMAT_DEFAULT = os.getenv("GUIDELINES_RESPONSE_FORMAT", "concise").lower()  # concise|detailed
    RESPONSE_PAGE_SIZE_DEFAULT = int(os.getenv("GUIDELINES_PAGE_SIZE", "10"))
    GLOBAL_RETRIEVAL_BUDGET_SECS = float(os.getenv("GUIDELINES_GLOBAL_BUDGET_SECS", "8.0"))
    PER_DOMAIN_SOFT_BUDGET_SECS = float(os.getenv("GUIDELINES_PER_DOMAIN_BUDGET_SECS", "1.5"))
    
    # Guidelines Sources - Domain mapping for filtering
    GUIDELINE_SOURCES: Dict[str, str] = {
        "gwern.net": "Hamming on research methodology and important problems",
        "lesswrong.com": "Research project selection and evaluation", 
        "colah.github.io": "Research taste and judgment",
        "01.me": "Research taste development",
        "arxiv.org": "Academic papers on research methodology",
        "lifescied.org": "Research process and methodology",
        "trendspider.com": "ML research framing",
        "news.ycombinator.com": "Community discussion on research",
        "cuhk.edu.hk": "Research taste academic perspectives",
        "michaelnielsen.org": "Research methodology principles and effective research",
        "febs.onlinelibrary.wiley.com": "Academic research practices and methodology",
        "researchgate.net": "Research methodology guides and best practices",
        "gigazine.net": "AI research impact and methodology",
        "academic.oup.com": "Academic research practices and methodology",
        "thoughtforms.life": "Student advice and research guidance",
        "letters.lossfunk.com": "Research methodology and good science manifesto",
        "alignmentforum.org": "Research process and ML paper writing guidance",
        "neelnanda.io": "Mechanistic interpretability and research methodology",
        "joschu.net": "ML research methodology and best practices",
        # Additional high-quality sources
        "cs.cmu.edu": "Computer science research methodology and advice",
        "stanford.edu": "Stanford research methodology and PhD guidance",
        "mit.edu": "MIT research methodology and academic guidance",
        "berkeley.edu": "Berkeley research methodology and PhD advice",
        "princeton.edu": "Princeton research guidance and methodology",
        "harvard.edu": "Harvard research methodology and academic guidance",
        "cam.ac.uk": "Cambridge University research methodology",
        "ox.ac.uk": "Oxford University research guidance",
        "ethz.ch": "ETH Zurich research methodology",
        "nature.com": "Nature journal research methodology articles",
        "science.org": "Science journal research methodology",
        "cell.com": "Cell press research methodology",
        "pnas.org": "PNAS research methodology and scientific practice",
        "ams.org": "American Mathematical Society research guidance",
        "acm.org": "ACM research methodology and computing practices",
        "ieee.org": "IEEE research methodology and engineering practices"
    }
    
    # Specific URLs for direct fetching if needed
    GUIDELINE_URLS: List[str] = [
        "https://gwern.net/doc/science/1986-hamming",
        "https://www.lesswrong.com/posts/kDsywodAKgQAAAxE8/how-not-to-choose-a-research-project",
        "https://news.ycombinator.com/item?id=35776480",
        "https://trendspider.com/learning-center/framing-machine-learning-research/",
        "https://arxiv.org/abs/2412.05683",
        "https://www.lifescied.org/doi/10.1187/cbe.20-12-0276",
        "https://arxiv.org/abs/2304.05585",
        "https://colah.github.io/notes/taste/",
        "https://01.me/en/2024/04/research-taste/",
        "https://home.ie.cuhk.edu.hk/~dmchiu/research_taste.pdf",
        "http://michaelnielsen.org/blog/principles-of-effective-research/",
        "https://febs.onlinelibrary.wiley.com/doi/10.1111/febs.15755",
        "https://www.researchgate.net/publication/31052323_Best_Practices_Research_A_Methodological_Guide_for_the_Perplexed",
        "https://gigazine.net/gsc_news/en/20240926-how-to-impactful-ai-research/",
        "https://academic.oup.com/icesjms/article/82/6/fsae121/7754918",
        "https://thoughtforms.life/what-advice-do-i-give-to-my-students/",
        "https://letters.lossfunk.com/p/what-is-research-and-how-to-do-it",
        "https://letters.lossfunk.com/p/manifesto-for-doing-good-science",
        "https://www.alignmentforum.org/posts/hjMy4ZxS5ogA9cTYK/how-i-think-about-my-research-process-explore-understand",
        "https://www.alignmentforum.org/posts/Xt8tMtwfsLo2jRCEj/highly-opinionated-advice-on-how-to-write-ml-papers",
        "https://www.neelnanda.io/mechanistic-interpretability/getting-started",
        "http://joschu.net/blog/opinionated-guide-ml-research.html"
    ]

    # Optional: concise per-source "thesis" blurbs to improve semantic matching
    GUIDELINE_THESES: Dict[str, str] = {
        # Exact URLs
        "https://gwern.net/doc/science/1986-hamming": "Hamming: Focus on important problems; taste comes from problem selection and persistence.",
        "https://www.lesswrong.com/posts/kDsywodAKgQAAAxE8/how-not-to-choose-a-research-project": "LessWrong: Avoid seductive but low-impact projects; choose tractable, impactful questions.",
        "https://trendspider.com/learning-center/framing-machine-learning-research/": "Framing ML research: Define problem framing, scope, and evaluation to maximize impact.",
        "https://arxiv.org/abs/2412.05683": "Paper: Recent guidance on research methodology and evaluation (check for updates).",
        "https://www.lifescied.org/doi/10.1187/cbe.20-12-0276": "LifeSciEd: Scientific process is complex; emphasizes iteration, reflection, and transparency.",
        "https://arxiv.org/abs/2304.05585": "Paper: On best practices/reproducibility in ML research (verify scope).",
        "https://colah.github.io/notes/taste/": "Colah: Research taste can be trained via deliberate practice and concrete exercises.",
        "https://01.me/en/2024/04/research-taste/": "01.me: Practical advice for cultivating research taste and judgment.",
        "https://home.ie.cuhk.edu.hk/~dmchiu/research_taste.pdf": "CUHK: Academic perspective on research taste and problem selection.",
        "http://michaelnielsen.org/blog/principles-of-effective-research/": "Nielsen: Principles of effective research—focus, feedback, and personal fit.",
        "https://febs.onlinelibrary.wiley.com/doi/10.1111/febs.15755": "FEBS: Scientific practice guidance; writing and methodology considerations.",
        "https://www.researchgate.net/publication/31052323_Best_Practices_Research_A_Methodological_Guide_for_the_Perplexed": "Best practices guide: methodology fundamentals and pitfalls to avoid.",
        "https://gigazine.net/gsc_news/en/20240926-how-to-impactful-ai-research/": "Impactful AI research: Focus on real progress signals over vanity metrics.",
        "https://academic.oup.com/icesjms/article/82/6/fsae121/7754918": "ICESJMS: Research practices and methodology in applied sciences.",
        "https://thoughtforms.life/what-advice-do-i-give-to-my-students/": "Student advice: Practical mentoring notes on early research decisions.",
        "https://letters.lossfunk.com/p/what-is-research-and-how-to-do-it": "What is research: Pragmatic definition and approach; reduce confusion and start building.",
        "https://letters.lossfunk.com/p/manifesto-for-doing-good-science": "Manifesto: Clarity, rigor, transparency, and usefulness as north stars.",
        "https://www.alignmentforum.org/posts/hjMy4ZxS5ogA9cTYK/how-i-think-about-my-research-process-explore-understand": "Research process: Explore→Understand loop and hypothesis refinement.",
        "https://www.alignmentforum.org/posts/Xt8tMtwfsLo2jRCEj/highly-opinionated-advice-on-how-to-write-ml-papers": "ML writing: Opinionated advice on framing, contributions, and clarity.",
        "https://www.neelnanda.io/mechanistic-interpretability/getting-started": "Mechanistic interpretability: Getting started path and resources.",
        "http://joschu.net/blog/opinionated-guide-ml-research.html": "Schulman: Opinionated ML research guide—focus on valuable problems and crisp experiments.",
    }

    @classmethod
    def thesis_for_url(cls, url: str) -> str:
        """Return a short thesis blurb for a curated URL if available, else domain-level blurb."""
        try:
            if url in cls.GUIDELINE_THESES:
                return cls.GUIDELINE_THESES[url]
            from urllib.parse import urlparse
            parsed = urlparse(url)
            dom = (parsed.netloc or "").lower()
            # Try any URL in same domain to inherit a thesis
            for u, t in cls.GUIDELINE_THESES.items():
                try:
                    p = urlparse(u)
                    if (p.netloc or "").lower() == dom:
                        return t
                except Exception:
                    continue
            return ""
        except Exception:
            return ""

    @classmethod
    def urls_by_domain(cls) -> Dict[str, List[str]]:
        """Group curated guideline URLs by domain.

        Returns:
            Mapping of domain -> list of URLs from GUIDELINE_URLS.
        """
        mapping: Dict[str, List[str]] = {}
        for url in cls.GUIDELINE_URLS:
            try:
                parsed = urlparse(url)
                domain = (parsed.netloc or "").lower()
                if not domain:
                    continue
                mapping.setdefault(domain, []).append(url)
            except Exception:
                # Ignore malformed URLs in config
                continue
        return mapping
    
    @classmethod
    def get_search_queries(cls, topic: str) -> List[str]:
        """Generate targeted search queries for different guideline sources."""
        return [
            f"site:gwern.net {topic} research methodology",
            f"site:lesswrong.com {topic} research project", 
            f"site:colah.github.io {topic} research taste",
            f"site:01.me {topic} research taste",
            f"{topic} research methodology site:arxiv.org",
            f"site:lifescied.org {topic} research process",
            f"site:cuhk.edu.hk {topic} research taste",
            f"site:michaelnielsen.org {topic} research",
            f"site:letters.lossfunk.com {topic} research",
            f"site:alignmentforum.org {topic} research",
            f"site:neelnanda.io {topic} research",
            f"site:joschu.net {topic} research",
            # Additional university and institutional sources
            f"site:stanford.edu {topic} research methodology",
            f"site:mit.edu {topic} research methodology",
            f"site:berkeley.edu {topic} research methodology",
            f"site:harvard.edu {topic} research methodology",
            f"site:cmu.edu {topic} research methodology",
            f"site:princeton.edu {topic} research guidance",
            # Journal and society sources
            f"site:nature.com {topic} research methodology",
            f"site:science.org {topic} research methodology",
            f"site:pnas.org {topic} scientific research"
        ]

    @classmethod
    def build_queries(cls, topic: str, domain: str, mode: str = None) -> List[str]:
        """Build domain-scoped queries for the given topic.

        Args:
            topic: user topic
            domain: domain to target (e.g., 'gwern.net')
            mode: 'fast'|'exhaustive' determines breadth of query variations
        """
        effective_mode = (mode or cls.DEFAULT_MODE).lower()
        base = [f"site:{domain} {topic}"]
        if effective_mode == "fast":
            return base
        # exhaustive: add a few variants
        return base + [
            f"site:{domain} {topic} research",
            f"site:{domain} {topic} methodology",
            f"site:{domain} {topic} advice",
        ]
