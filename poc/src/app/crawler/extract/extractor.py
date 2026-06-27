import re
from typing import Optional, Dict
from selectolax.parser import HTMLParser


class ExtractResult:
    def __init__(self, title: str, text: str, description: str, metadata: Dict):
        self.title = title
        self.text = text
        self.description = description
        self.metadata = metadata


class Extractor:
    """
    Extracts:
    - title
    - main text
    - meta description
    - metadata (h1, h2, canonical, og:title, og:description)
    """

    def extract(self, html: str) -> Optional[ExtractResult]:
        if not html or len(html.strip()) < 50:
            return None

        tree = HTMLParser(html)

        # -------------------------
        # 1. TITLE
        # -------------------------
        title = ""
        title_tag = tree.css_first("title")
        if title_tag:
            title = title_tag.text().strip()

        # Fallback: og:title
        og_title = tree.css_first("meta[property='og:title']")
        if og_title and og_title.attributes.get("content"):
            title = og_title.attributes["content"].strip()

        # -------------------------
        # 2. META DESCRIPTION
        # -------------------------
        description = ""
        desc_tag = tree.css_first("meta[name='description']")
        if desc_tag and desc_tag.attributes.get("content"):
            description = desc_tag.attributes["content"].strip()

        # Fallback: og:description
        og_desc = tree.css_first("meta[property='og:description']")
        if og_desc and og_desc.attributes.get("content"):
            description = og_desc.attributes["content"].strip()

        # -------------------------
        # 3. MAIN TEXT EXTRACTION
        # -------------------------
        text = self._extract_main_text(tree)

        # -------------------------
        # 4. METADATA
        # -------------------------
        metadata = {
            "h1": [h.text().strip() for h in tree.css("h1")],
            "h2": [h.text().strip() for h in tree.css("h2")],
            "canonical": self._get_canonical(tree),
            "og_title": title,
            "og_description": description,
        }

        return ExtractResult(
            title=title,
            text=text,
            description=description,
            metadata=metadata
        )

    # ----------------------------------------------------
    # Helpers
    # ----------------------------------------------------

    def _extract_main_text(self, tree: HTMLParser) -> str:
        """
        Extract readable text from <p>, <article>, <div> blocks.
        Removes menus, footers, scripts, nav, etc.
        """

        # Remove noise
        for selector in ["script", "style", "nav", "footer", "header", "noscript"]:
            for tag in tree.css(selector):
                tag.decompose()

        # Collect text blocks
        paragraphs = []

        for p in tree.css("p"):
            txt = p.text().strip()
            if len(txt) > 40:  # filter out junk
                paragraphs.append(txt)

        # Fallback: article text
        if not paragraphs:
            article = tree.css_first("article")
            if article:
                raw = article.text().strip()
                return self._clean_text(raw)

        # Join paragraphs
        full_text = "\n".join(paragraphs)
        return self._clean_text(full_text)

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _get_canonical(self, tree: HTMLParser) -> Optional[str]:
        tag = tree.css_first("link[rel='canonical']")
        if tag and tag.attributes.get("href"):
            return tag.attributes["href"]
        return None
