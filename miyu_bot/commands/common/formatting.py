def format_info(info_entries: dict):
    return '\n'.join(f'{k}: {v}' for k, v in info_entries.items() if v)