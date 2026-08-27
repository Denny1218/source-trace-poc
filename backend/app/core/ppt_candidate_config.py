"""PPT Candidate scoring configuration (STEP 5)."""

import os

PPT_CANDIDATE_SCORE_CONFIG = {
    "filename_date": 35,
    "modified_at": 10,
    "filename_keyword": 30,
    "folder_keyword": 15,
    "equipment_context": 10,
}

PPT_CANDIDATE_LIMIT = int(os.getenv("PPT_CANDIDATE_LIMIT", "30"))
