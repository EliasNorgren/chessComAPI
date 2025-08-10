import threading
import uuid

class EntryCache: 
    def __init__(self):
        self.computed_entries = {} 
        self.computed_entries_lock = threading.Lock()
    
    def get_entry(self, uuid):
        if not isinstance(uuid, str):
            raise ValueError("UUID must be a string")
        with self.computed_entries_lock:
            return self.computed_entries.get(uuid, None)

    def set_entry(self, uuid, entry):
        if not isinstance(uuid, str):
            raise ValueError("UUID must be a string")
        with self.computed_entries_lock:
            self.computed_entries[uuid] = entry

    def drop_entry(self, uuid):
        if not isinstance(uuid, str):
            raise ValueError("UUID must be a string")
        with self.computed_entries_lock:
            if uuid in self.computed_entries:
                del self.computed_entries[uuid]
    
    def print_entries(self):
        print("Current entries in cache:")
        with self.computed_entries_lock:
            for uuid, entry in self.computed_entries.items():
                print(f"UUID: {uuid}, Entry: {entry}")