"""
embedding_index.py — PRISM Semantic Product Index (RAG layer).

WHY THIS MODULE EXISTS:
Text keyword matching is brittle: searching for "phone" retrieves chargers because
they share the word "phone charger". Embedding-based retrieval computes the MEANING
of a query and finds products that are semantically closest — a phone vs a charger
have very different embeddings even though they co-occur as text.

This module provides two backend options (auto-detected):
  PRIMARY:  fastembed (ONNX-based, no PyTorch, Windows-safe, ~50MB model)
  FALLBACK: numpy cosine similarity over pre-computed embeddings (no FAISS needed)
  DISABLED: graceful empty-results if neither is available

Used by product_matcher.py for ALL query types:
  - Specific-item asks: embed the item → retrieve exact matches, score accessories lower
  - Context queries:    embed each product_need phrase → retrieve semantically matching products

Model: BAAI/bge-small-en-v1.5 via fastembed (384-dim, ONNX-quantised, fast inference)

Libraries: fastembed (MIT), numpy (BSD), json (stdlib)
"""

import os
import json
import logging
import pickle
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

_INDEX_PATH = os.path.join(os.path.dirname(__file__), "../data/prism_emb_index.pkl")

# ── Optional imports — try fastembed first ────────────────────────────────────
_FASTEMBED_AVAILABLE = False
_NUMPY_AVAILABLE = False

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    pass

try:
    from fastembed import TextEmbedding
    _FASTEMBED_AVAILABLE = True
    logger.info("[EmbeddingIndex] fastembed available — ONNX-based embeddings enabled.")
except ImportError:
    if _NUMPY_AVAILABLE:
        logger.warning(
            "[EmbeddingIndex] fastembed not installed. "
            "Install with: pip install fastembed  "
            "Falling back to TF-IDF cosine similarity."
        )
    else:
        logger.warning(
            "[EmbeddingIndex] Neither fastembed nor numpy available. "
            "RAG disabled — using keyword matching only."
        )

_EMBEDDING_AVAILABLE = _FASTEMBED_AVAILABLE and _NUMPY_AVAILABLE

# ── TF-IDF fallback (when fastembed not available) ────────────────────────────
# Lightweight bag-of-words cosine similarity using numpy only (no ML deps)
_TFIDF_AVAILABLE = False
if _NUMPY_AVAILABLE and not _FASTEMBED_AVAILABLE:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        _TFIDF_AVAILABLE = True
        logger.info("[EmbeddingIndex] scikit-learn TF-IDF available as fallback.")
    except ImportError:
        pass


def _product_to_text(product: Dict[str, Any]) -> str:
    """
    Converts a product dict to a rich text string for embedding.
    Name is repeated for emphasis; tags and description add context.
    """
    parts = []

    name = (product.get("name") or "").strip()
    if name:
        parts.append(name)
        parts.append(name)  # repeat for emphasis

    cat = (product.get("category") or "").replace("_", " ")
    subcat = (product.get("subcategory") or "").replace("_", " ")
    brand = (product.get("brand") or "")
    desc = (product.get("description") or "")

    if cat:
        parts.append(cat)
    if subcat and subcat != "general":
        parts.append(subcat)
    if brand and brand != "Generic":
        parts.append(brand)
    if desc:
        parts.append(desc[:200])

    tags = product.get("tags", [])
    if isinstance(tags, list):
        parts.extend(tags[:6])
    elif isinstance(tags, str):
        try:
            parsed = json.loads(tags)
            parts.extend(parsed[:6])
        except Exception:
            pass

    return " ".join(filter(None, parts))


class PRISMEmbeddingIndex:
    """
    Singleton semantic product index for PRISM.

    Backends (auto-detected):
      1. fastembed  — ONNX-quantised BGE model, ~50MB, fast, Windows-safe
      2. TF-IDF     — scikit-learn fallback, no ML download needed
      3. Disabled   — returns empty results, caller falls back to keyword search
    """

    _instance: Optional["PRISMEmbeddingIndex"] = None
    _fe_model: Optional[Any] = None   # fastembed TextEmbedding singleton
    _tfidf_model: Optional[Any] = None

    def __init__(self):
        self._embeddings: Optional["np.ndarray"] = None   # (N, D) matrix
        self._id_map: List[str] = []                      # row → product_id
        self._built = False

    @classmethod
    def get_instance(cls) -> "PRISMEmbeddingIndex":
        if cls._instance is None:
            cls._instance = PRISMEmbeddingIndex()
        return cls._instance

    @classmethod
    def invalidate(cls):
        """Force a full re-index after catalog rebuild."""
        cls._instance = None
        if os.path.exists(_INDEX_PATH):
            try:
                os.remove(_INDEX_PATH)
            except Exception:
                pass
        logger.info("[EmbeddingIndex] Invalidated — will rebuild on next search.")

    # ── Model loading ─────────────────────────────────────────────────────────

    def _get_fe_model(self):
        if PRISMEmbeddingIndex._fe_model is None and _FASTEMBED_AVAILABLE:
            logger.info("[EmbeddingIndex] Loading fastembed model BAAI/bge-small-en-v1.5...")
            PRISMEmbeddingIndex._fe_model = TextEmbedding(
                model_name="BAAI/bge-small-en-v1.5",
                # threads=2,
            )
            logger.info("[EmbeddingIndex] fastembed model ready.")
        return PRISMEmbeddingIndex._fe_model

    def _get_tfidf(self):
        return PRISMEmbeddingIndex._tfidf_model

    # ── Encode ────────────────────────────────────────────────────────────────

    def _encode_fastembed(self, texts: List[str]) -> "np.ndarray":
        model = self._get_fe_model()
        if model is None:
            return None
        embeddings = list(model.embed(texts))
        arr = np.array(embeddings, dtype="float32")
        # Normalise to unit length (cosine = dot product)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return arr / norms

    def _encode(self, texts: List[str]) -> Optional["np.ndarray"]:
        if _FASTEMBED_AVAILABLE and _NUMPY_AVAILABLE:
            return self._encode_fastembed(texts)
        return None

    # ── Build ─────────────────────────────────────────────────────────────────

    def build_index(self, products: List[Dict[str, Any]]) -> bool:
        """
        Encodes all products and saves embeddings to disk.
        Returns True on success.
        """
        if not _EMBEDDING_AVAILABLE:
            # Try TF-IDF fallback
            if _TFIDF_AVAILABLE:
                return self._build_tfidf(products)
            return False

        logger.info(f"[EmbeddingIndex] Encoding {len(products)} products...")

        texts = [_product_to_text(p) for p in products]
        ids = [str(p.get("id", "")) for p in products]

        try:
            embeddings = self._encode(texts)
            if embeddings is None:
                return False

            self._embeddings = embeddings
            self._id_map = ids
            self._built = True

            # Save to disk
            with open(_INDEX_PATH, "wb") as f:
                pickle.dump({"embeddings": embeddings, "id_map": ids}, f)
            logger.info(f"[EmbeddingIndex] Saved {len(ids)} embeddings (dim={embeddings.shape[1]})")
            return True

        except Exception as e:
            logger.error(f"[EmbeddingIndex] build_index error: {e}")
            return False

    def _build_tfidf(self, products: List[Dict[str, Any]]) -> bool:
        """TF-IDF fallback build."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            texts = [_product_to_text(p) for p in products]
            ids = [str(p.get("id", "")) for p in products]

            vectorizer = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), sublinear_tf=True)
            matrix = vectorizer.fit_transform(texts)  # sparse
            # Normalise rows
            from sklearn.preprocessing import normalize
            matrix = normalize(matrix)

            PRISMEmbeddingIndex._tfidf_model = vectorizer
            self._embeddings = matrix
            self._id_map = ids
            self._built = True
            logger.info(f"[EmbeddingIndex] TF-IDF index built ({len(ids)} products)")
            return True
        except Exception as e:
            logger.error(f"[EmbeddingIndex] TF-IDF build error: {e}")
            return False

    def _try_load_from_disk(self) -> bool:
        """Load pre-built embeddings from disk."""
        if not _NUMPY_AVAILABLE:
            return False
        if not os.path.exists(_INDEX_PATH):
            return False
        try:
            with open(_INDEX_PATH, "rb") as f:
                data = pickle.load(f)
            self._embeddings = data["embeddings"]
            self._id_map = data["id_map"]
            self._built = True
            logger.info(f"[EmbeddingIndex] Loaded from disk ({len(self._id_map)} products)")
            return True
        except Exception as e:
            logger.warning(f"[EmbeddingIndex] Disk load failed: {e}")
            return False

    def _ensure_built(self, products_loader=None) -> bool:
        if self._built:
            return True
        if self._try_load_from_disk():
            return True
        if products_loader is not None:
            products = products_loader()
            return self.build_index(products)
        return False

    # ── Search ────────────────────────────────────────────────────────────────

    def _cosine_search(self, query_emb: "np.ndarray", k: int) -> List[Tuple[str, float]]:
        """Dot product search against the stored embedding matrix."""
        if self._embeddings is None:
            return []
        try:
            # Dense embeddings: matrix multiply
            import scipy.sparse
            is_sparse = scipy.sparse.issparse(self._embeddings)
            if is_sparse:
                scores = (self._embeddings @ query_emb.reshape(-1, 1)).toarray().flatten()
            else:
                scores = self._embeddings @ query_emb  # (N,)

            top_k = min(k, len(scores))
            top_indices = np.argpartition(scores, -top_k)[-top_k:]
            top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]

            return [
                (self._id_map[i], float(scores[i]))
                for i in top_indices
                if i < len(self._id_map)
            ]
        except Exception as e:
            logger.error(f"[EmbeddingIndex] cosine_search error: {e}")
            return []

    def _encode_query(self, query: str) -> Optional["np.ndarray"]:
        """Encodes a single query string."""
        if _FASTEMBED_AVAILABLE and _NUMPY_AVAILABLE:
            emb = self._encode_fastembed([query])
            if emb is not None:
                return emb[0]
        elif _TFIDF_AVAILABLE and self._get_tfidf() is not None:
            try:
                from sklearn.preprocessing import normalize
                vec = self._get_tfidf().transform([query])
                vec = normalize(vec)
                return np.asarray(vec.todense()).flatten()
            except Exception:
                pass
        return None

    def search(
        self,
        query: str,
        k: int = 50,
        products_loader=None,
    ) -> List[Tuple[str, float]]:
        """
        Returns top-k (product_id, cosine_score) pairs.
        Empty list if index not available.
        """
        if not self._ensure_built(products_loader):
            return []
        q_emb = self._encode_query(query)
        if q_emb is None:
            return []
        return self._cosine_search(q_emb, k)

    def search_batch(
        self,
        queries: List[str],
        k_per_query: int = 30,
        products_loader=None,
    ) -> Dict[str, float]:
        """
        Multi-query search. Returns {product_id: max_score} across all queries.
        Used for context queries where product_needs is a list of phrases.
        """
        if not queries:
            return {}
        if not self._ensure_built(products_loader):
            return {}

        merged: Dict[str, float] = {}
        for query in queries:
            q_emb = self._encode_query(query)
            if q_emb is None:
                continue
            results = self._cosine_search(q_emb, k_per_query)
            for pid, score in results:
                if pid not in merged or score > merged[pid]:
                    merged[pid] = score

        return merged

    def get_embedding(self, text: str) -> Optional["np.ndarray"]:
        """Returns a normalised embedding for a single text string."""
        return self._encode_query(text)

    def cosine_similarity(self, emb_a, emb_b) -> float:
        """Cosine similarity between two unit-normalised embedding vectors."""
        if not _NUMPY_AVAILABLE or emb_a is None or emb_b is None:
            return 0.0
        try:
            # Handle sparse vectors from TF-IDF
            import scipy.sparse
            if scipy.sparse.issparse(emb_a):
                emb_a = np.asarray(emb_a.todense()).flatten()
            if scipy.sparse.issparse(emb_b):
                emb_b = np.asarray(emb_b.todense()).flatten()
            return float(np.dot(emb_a, emb_b))
        except Exception:
            return 0.0

    @property
    def is_available(self) -> bool:
        return (_FASTEMBED_AVAILABLE or _TFIDF_AVAILABLE) and _NUMPY_AVAILABLE

    @property
    def is_built(self) -> bool:
        return self._built


# ── Module-level convenience functions ───────────────────────────────────────

def get_index() -> PRISMEmbeddingIndex:
    return PRISMEmbeddingIndex.get_instance()


def is_rag_available() -> bool:
    return _FASTEMBED_AVAILABLE and _NUMPY_AVAILABLE
