ROSTER_DISCOVERY_SCHEMA = {
    "type": "object",
    "properties": {
        "school_name": {"type": "string"},
        "discipline": {"type": "string"},
        "roster_source": {"type": "string"},
        "roster_status": {
            "type": "string",
            "enum": ["completed", "incomplete"],
        },
        "roster_note": {"type": "string"},
        "roster_members": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "displayed_title": {"type": "string"},
                    "profile_url": {"type": "string"},
                },
                "required": ["name", "displayed_title", "profile_url"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "school_name",
        "discipline",
        "roster_source",
        "roster_status",
        "roster_note",
        "roster_members",
    ],
    "additionalProperties": False,
}


SCHOOL_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "school_name": {"type": "string"},
        "roster_source": {"type": "string"},
        "school_status": {
            "type": "string",
            "enum": ["completed", "incomplete"],
        },
        "school_note": {"type": "string"},
        "faculty_classifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "candidate_name": {"type": "string"},
                    "discipline": {"type": "string"},
                    "current_rank": {"type": "string"},
                    "decision": {
                        "type": "string",
                        "enum": ["included", "excluded", "needs_review"],
                    },
                    "exclusion_or_review_reason": {"type": "string"},
                    "phd_year": {"type": ["integer", "null"]},
                    "first_year_of_rank": {"type": ["integer", "null"]},
                    "first_year_basis": {
                        "type": "string",
                        "enum": [
                            "exact_promotion_appointment",
                            "joined_school_at_rank",
                            "earliest_official_title_year",
                            "school_start_fallback",
                            "unknown",
                            "not_applicable",
                        ],
                    },
                    "profile_or_cv_url": {"type": "string"},
                    "current_source": {"type": "string"},
                    "evidence_urls": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                    "notes": {"type": "string"},
                },
                "required": [
                    "candidate_name",
                    "discipline",
                    "current_rank",
                    "decision",
                    "exclusion_or_review_reason",
                    "phd_year",
                    "first_year_of_rank",
                    "first_year_basis",
                    "profile_or_cv_url",
                    "current_source",
                    "evidence_urls",
                    "confidence",
                    "notes",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "school_name",
        "roster_source",
        "school_status",
        "school_note",
        "faculty_classifications",
    ],
    "additionalProperties": False,
}
