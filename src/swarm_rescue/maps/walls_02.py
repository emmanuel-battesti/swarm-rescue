from spg_overlay.normal_wall import NormalWall, NormalBox


# Dimension of the map : (1113,750)
# Dimension factor : 1.048951048951049
def add_boxes(playground):
    # box 0
    playground.add_element(NormalBox(up_left_point=(560, 303),
                                     width=130, height=100))
    # box 1
    # playground.add_element(NormalBox(up_left_point=(939, 58),
    #                                  width=129, height=142))
    # box 2
    playground.add_element(NormalBox(up_left_point=(0, 0),
                                     width=428, height=150))
    # box 3
    playground.add_element(NormalBox(up_left_point=(0, 595),
                                     width=430, height=150))

    # box top
    playground.add_element(NormalBox(up_left_point=(423, 0),
                                     width=693, height=11))

    # box right
    playground.add_element(NormalBox(up_left_point=(1100, 0),
                                     width=20, height=745))

    # box bottom
    playground.add_element(NormalBox(up_left_point=(428, 732),
                                     width=695, height=13))

    # box left
    playground.add_element(NormalBox(up_left_point=(0, 147),
                                     width=12, height=450))


def add_walls(playground):
    # vertical wall 0
    playground.add_element(NormalWall(start_point=(426, 11),
                                      end_point=(426, 150)))
    # horizontal wall 1
    playground.add_element(NormalWall(start_point=(427, 12),
                                      end_point=(704, 12)))
    # vertical wall 2
    playground.add_element(NormalWall(start_point=(702, 12),
                                      end_point=(702, 146)))
    # horizontal wall 3
    playground.add_element(NormalWall(start_point=(705, 12),
                                      end_point=(892, 12)))
    # vertical wall 4
    playground.add_element(NormalWall(start_point=(890, 12),
                                      end_point=(890, 113)))
    # horizontal wall 5
    playground.add_element(NormalWall(start_point=(893, 13),
                                      end_point=(1103, 13)))
    # vertical wall 6
    playground.add_element(NormalWall(start_point=(1101, 13),
                                      end_point=(1101, 739)))
    # vertical wall 7
    # playground.add_element(NormalWall(start_point=(942, 60),
    #                                   end_point=(942, 196)))
    # # horizontal wall 8
    # playground.add_element(NormalWall(start_point=(943, 61),
    #                                   end_point=(1065, 61)))

    # vertical wall 9
    # playground.add_element(NormalWall(start_point=(1063, 61),
    #                                   end_point=(1063, 196)))

    # vertical wall 10
    playground.add_element(NormalWall(start_point=(11, 146),
                                      end_point=(11, 260)))
    # horizontal wall 11
    playground.add_element(NormalWall(start_point=(12, 147),
                                      end_point=(155, 147)))
    # vertical wall 12
    playground.add_element(NormalWall(start_point=(153, 147),
                                      end_point=(153, 260)))
    # vertical wall 13
    playground.add_element(NormalWall(start_point=(156, 146),
                                      end_point=(156, 409)))
    # horizontal wall 14
    playground.add_element(NormalWall(start_point=(157, 147),
                                      end_point=(425, 147)))
    # vertical wall 15
    playground.add_element(NormalWall(start_point=(890, 235),
                                      end_point=(890, 174)))
    # horizontal wall 16
    playground.add_element(NormalWall(start_point=(703, 233),
                                      end_point=(889, 233)))
    # # horizontal wall 17
    # playground.add_element(NormalWall(start_point=(942, 194),
    #                                   end_point=(1064, 194)))
    # vertical wall 18
    playground.add_element(NormalWall(start_point=(702, 213),
                                      end_point=(702, 237)))
    # horizontal wall 19
    playground.add_element(NormalWall(start_point=(702, 236),
                                      end_point=(892, 236)))
    # vertical wall 20
    playground.add_element(NormalWall(start_point=(890, 236),
                                      end_point=(890, 481)))
    # vertical wall 21
    playground.add_element(NormalWall(start_point=(254, 274),
                                      end_point=(254, 234)))
    # horizontal wall 22
    playground.add_element(NormalWall(start_point=(254, 236),
                                      end_point=(427, 236)))
    # horizontal wall 23
    playground.add_element(NormalWall(start_point=(255, 239),
                                      end_point=(426, 239)))
    # vertical wall 24
    playground.add_element(NormalWall(start_point=(424, 239),
                                      end_point=(424, 599)))
    # vertical wall 25
    playground.add_element(NormalWall(start_point=(254, 240),
                                      end_point=(254, 275)))
    # horizontal wall 26
    playground.add_element(NormalWall(start_point=(11, 258),
                                      end_point=(28, 258)))
    # horizontal wall 27
    playground.add_element(NormalWall(start_point=(121, 258),
                                      end_point=(154, 258)))
    # vertical wall 28
    playground.add_element(NormalWall(start_point=(10, 260),
                                      end_point=(10, 516)))
    # horizontal wall 29
    playground.add_element(NormalWall(start_point=(12, 261),
                                      end_point=(27, 261)))
    # horizontal wall 30
    playground.add_element(NormalWall(start_point=(119, 261),
                                      end_point=(155, 261)))
    # vertical wall 31
    playground.add_element(NormalWall(start_point=(153, 261),
                                      end_point=(153, 408)))
    # vertical wall 32
    playground.add_element(NormalWall(start_point=(563, 305),
                                      end_point=(563, 400)))
    # horizontal wall 33
    playground.add_element(NormalWall(start_point=(564, 306),
                                      end_point=(687, 306)))
    # vertical wall 34
    playground.add_element(NormalWall(start_point=(685, 306),
                                      end_point=(685, 400)))
    # vertical wall 35
    playground.add_element(NormalWall(start_point=(254, 362),
                                      end_point=(254, 599)))
    # horizontal wall 36
    playground.add_element(NormalWall(start_point=(255, 597),
                                      end_point=(425, 597)))
    # vertical wall 37
    playground.add_element(NormalWall(start_point=(251, 363),
                                      end_point=(251, 599)))
    # horizontal wall 38
    playground.add_element(NormalWall(start_point=(155, 597),
                                      end_point=(250, 597)))
    # horizontal wall 39
    playground.add_element(NormalWall(start_point=(563, 398),
                                      end_point=(686, 398)))
    # horizontal wall 40
    playground.add_element(NormalWall(start_point=(425, 479),
                                      end_point=(760, 479)))
    # horizontal wall 41
    playground.add_element(NormalWall(start_point=(834, 479),
                                      end_point=(890, 479)))
    # vertical wall 42
    playground.add_element(NormalWall(start_point=(588, 481),
                                      end_point=(588, 647)))
    # vertical wall 43
    playground.add_element(NormalWall(start_point=(156, 490),
                                      end_point=(156, 526)))
    # vertical wall 44
    playground.add_element(NormalWall(start_point=(156, 516),
                                      end_point=(156, 491)))
    # horizontal wall 45
    playground.add_element(NormalWall(start_point=(11, 514),
                                      end_point=(152, 514)))
    # vertical wall 46
    playground.add_element(NormalWall(start_point=(11, 516),
                                      end_point=(11, 599)))
    # horizontal wall 47
    playground.add_element(NormalWall(start_point=(12, 517),
                                      end_point=(155, 517)))
    # horizontal wall 48
    playground.add_element(NormalWall(start_point=(11, 597),
                                      end_point=(155, 597)))
    # vertical wall 49
    playground.add_element(NormalWall(start_point=(429, 596),
                                      end_point=(429, 737)))
    # horizontal wall 50
    playground.add_element(NormalWall(start_point=(429, 735),
                                      end_point=(1092, 735)))
