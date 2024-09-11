from enum import Enum

class CarStatus(Enum):
    """
    Enum class to describe state of the car: Acceleration, Braking, Idling.
    """

    ACCELERATE = 1
    BRAKE = 2
    IDLE = 3