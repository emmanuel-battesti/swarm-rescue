def get_gps_values(drone):
    '''Return GPS values if available, else return None'''
    if drone.gps_is_disabled():
        return None, None
    else:
        return drone.measured_gps_position()[0], drone.measured_gps_position()[1]