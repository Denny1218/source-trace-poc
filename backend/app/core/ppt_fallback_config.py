"""PPT progressive fallback configuration (STEP 6 change-item search)."""

import os

# Parse up to N documents per fallback batch (UNC latency ~1-3s/doc in ops tests).
PPT_FALLBACK_BATCH_SIZE = int(os.getenv("PPT_FALLBACK_BATCH_SIZE", "3"))

# Max total fallback documents parsed in one analysis request.
# 15 docs × ~2s keeps request under ~30s extra on typical server/UNC.
PPT_FALLBACK_MAX_DOCUMENTS = int(os.getenv("PPT_FALLBACK_MAX_DOCUMENTS", "15"))

# Stop fallback when this many change-item hits are found.
PPT_FALLBACK_RESULT_LIMIT = int(os.getenv("PPT_FALLBACK_RESULT_LIMIT", "20"))

CHANGE_ITEM_CANDIDATE_LIMIT = int(os.getenv("CHANGE_ITEM_CANDIDATE_LIMIT", "30"))

CHANGE_ITEM_SCORE_CONFIG = {
    "change_title": 40,
    "source_function": 35,
    "to_be": 30,
    "csr_no": 25,
    "business_background": 20,
    "current_status": 20,
    "as_is": 20,
    "raw_text": 10,
}
