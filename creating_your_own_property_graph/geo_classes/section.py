from geo_classes.inclination import Inclination
from enum import Enum


class RoadTypes(Enum):
    PEDESTRIAN = 1
    CYCLEWAY = 2
    FOOTWAY = 3
    BRIDLEWAY = 4
    PATH = 5
    TRACK = 6
    SERVICE = 7
    LIVING_STREET = 8
    RESIDENTIAL = 9
    TRUNK = 10  # illegal
    PRIMARY = 11
    SECONDARY = 12
    TERTIARY = 13
    UNCLASSIFIED = 14
    MOTORWAY = 15  # illegal


class Section:
    def __init__(self, node_from: int, node_to: int, incline: Inclination, road_types: []):
        self.node_from = node_from
        self.node_to = node_to
        self.incline = incline
        road_types = []
