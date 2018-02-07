min_time = 60
max_time = 5184000
check = {
    "properties": {
        "name": {"type": "string"},
        "tags": {"type": "string"},
        "timeout": {"type": "number", "minimum": min_time, "maximum": max_time},
        "grace": {"type": "number", "minimum": min_time, "maximum": max_time},
        "nag": {"type": "number", "minimum": min_time, "maximum": max_time},
        "channels": {"type": "string"}
    }
}