"""PPT parsing and slide candidate configuration (STEP 6)."""

import os

PPT_PARSE_LIMIT = int(os.getenv("PPT_PARSE_LIMIT", "10"))
SLIDE_CANDIDATE_LIMIT = int(os.getenv("SLIDE_CANDIDATE_LIMIT", "50"))

# SHA-256 chunk size (64 KB)
FILE_HASH_CHUNK_SIZE = int(os.getenv("FILE_HASH_CHUNK_SIZE", "65536"))

SLIDE_CANDIDATE_SCORE_CONFIG = {
    "title_keyword": 40,
    "content_keyword": 35,
    "filename_keyword": 25,
}

FALLBACK_TITLE_MAX_LENGTH = 200
