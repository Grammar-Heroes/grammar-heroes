from enum import Enum

class AdventureState(str, Enum):
   IN_PROGRESS = "in_progress"
   SUCCESS = "success"
   FAILED = "failed"