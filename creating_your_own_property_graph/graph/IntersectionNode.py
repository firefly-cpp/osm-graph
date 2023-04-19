class IntersectionNode:
    def __init__(self, node_id, latitude, longitude, way_ids):
        self.node_id = node_id
        self.latitude = latitude
        self.longitude = longitude
        self.way_ids = way_ids
        self.label = "intersection"
