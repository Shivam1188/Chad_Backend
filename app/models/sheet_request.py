from dataclasses import dataclass


@dataclass
class SheetRequest:
    sheet_url: str
    collection: str
    force_reprocess: bool = False
