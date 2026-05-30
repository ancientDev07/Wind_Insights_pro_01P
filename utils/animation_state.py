# utils/animation_state.py
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal

class AnimationState(Enum):
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"

class AnimationStateManager(QObject):
    state_changed = pyqtSignal(AnimationState, str)
    
    def __init__(self):
        super().__init__()
        self._state = AnimationState.IDLE
    
    def set_loading(self, message="Processing..."):
        self._state = AnimationState.LOADING
        self.state_changed.emit(self._state, message)
    
    def set_success(self, message="Complete"):
        self._state = AnimationState.SUCCESS
        self.state_changed.emit(self._state, message)
    
    def set_error(self, message="Error occurred"):
        self._state = AnimationState.ERROR
        self.state_changed.emit(self._state, message)
    
    def reset(self):
        self._state = AnimationState.IDLE
        self.state_changed.emit(self._state, "")
