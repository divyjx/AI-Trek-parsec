# THIS IS AN EMPTY BOT

from constants import *
import math
from models.Action import Action
from models.Obstacle import Obstacle
from models.Point import Point
from models.State import State
import pickle
import random
import socket
import sys
from typing import List


#     agents: Dict[str, Agent]  # The player's agents
#     object_in_sight: Dict[str, List[ObjectSighting]]  # Agent : [ObjectSighting] ,Bullet: [ObjectSighting]  ,Wall: [
#     # ObjectSighting]
#     Alerts: List[Alert]  # List of alerts collisions, zone, bullet_hit etc
#     team: str
#     time: int
#     obstacles: List[Obstacle]  # List of obstacles in the environment
#     zone: List[Point]  # List of corners in the zone
#     safe_zone: List[Point]  # List of corners in the safe zone
#     is_zone_shrinking: bool  # True if zone is shrinking, False if zone is expanding
#     STRING = "Agents: {agents} \n Object in sight: {object_in_sight} \n Alerts: {alerts} \n Team: {team} \n Time: {" \
#              "time} \n Obstacles: {obstacles} \n Zone: {zone} \n Safe Zone: {safe_zone} \n Is Zone Shrinking: {" \
#              "is_zone_shrinking} "

# TODO: normalize the parameter Point
# update direction and view direction
def turn_left(curr_dir: Point) -> Point:
    return Point(-curr_dir.y, curr_dir.x)

def turn_right(curr_dir: Point) -> Point:
    return Point(curr_dir.y, -curr_dir.x)
    
def turn_back(curr_dir: Point) -> Point:
    return Point(-curr_dir.x, -curr_dir.y)

# fire
# red is opponent
def fire3(blue_location: Point, blue_direction: Point, red_location: Point, red_direction: Point) -> Point:
    red_location.sub(blue_location)
    alpha = (red_direction.get_angle() - red_location.get_angle())
    alpha = math.radians(alpha)
    theta = math.asin(math.sin(alpha) / 5)
    theta += math.radians(red_location.get_angle())
    # print(math.degrees(theta))
    return Point(math.cos(theta), math.sin(theta))

def fire2(blue_location: Point, blue_direction: Point, red_location: Point, red_direction: Point) -> Point:
    v1 = red_location
    v1.sub(blue_location)
    # print(v1)
    # red_direction.make_unit_magnitude()
    v1.add(red_direction)
    return v1

def find_center(safe_zone_corners: List[Point]):
    safe_zone_corners.sort(key=lambda item: item.x)
    x1, x2 = safe_zone_corners[0].x, safe_zone_corners[2].x
    safe_zone_corners.sort(key=lambda item: item.y)
    y1, y2 = safe_zone_corners[0].y, safe_zone_corners[2].y 
    return Point((x2 + x1)/2, (y2 + y1)/2)

def zone_check(blue_location: Point, blue_direction: Point, safe_zone_corners: List[Point]):
    xx, yy = blue_location.x, blue_location.y
    away = False
    safe_zone_corners.sort(key=lambda item: item.x)
    x1, x2 = safe_zone_corners[0].x, safe_zone_corners[2].x
    safe_zone_corners.sort(key=lambda item: item.y)
    y1, y2 = safe_zone_corners[0].y, safe_zone_corners[2].y 
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1 
    # print(x1, x2, y1, y2)
    if xx < x1+5 or xx > x2-5 or yy < y1+5 or yy > y2-5:
        away = True
    if away:
        return [Point((x2 + x1)/2 - xx, (y2 + y1)/2 - yy), True]
    return [Point(xx, yy), False]

def check_alerts(state: State) -> List[int]:
    agents_alert_list = []
    for alert in state.alerts:
        if alert.alert_type == COLLISION:
            agents_alert_list.append(alert.agent_id)
    return agents_alert_list

def explore(curr_dir: Point) -> Point:
    p = random.uniform(0, 1)
    if p < 0.7:
        direction = turn_left(curr_dir)
    # elif p < 0.6:
    #     direction = turn_right(curr_dir)
    else:
        direction = turn_back(curr_dir)
    return direction

def tick(state: State) -> List[Action]:
    safe_zone = state.safe_zone
    actions = []
            
    for agent_id in state.agents:
        # choose an action for this agent
        agent = state.agents[agent_id]

        # TODO: if stuck then update direction
        if agent_id in check_alerts(state):
            actions.append(Action(agent_id, UPDATE_DIRECTION, explore(agent.get_direction())))
            continue

        # if out of zone then update direction
        zone_var = zone_check(agent.get_location(), agent.get_direction(), safe_zone)
        if zone_var[1]:
            # print("Out")
            actions.append(Action(agent_id, UPDATE_DIRECTION, zone_var[0]))
            continue

        # if enemy in sight then fire
        objects_sighted = state.object_in_sight.get(agent_id)
        # print(objects_sighted) # {'Agents':[], 'Bullets':[]}
        opp_list = objects_sighted['Agents']
        bullet_list = objects_sighted['Bullets']
        shoot = False
        for opp in opp_list:
            fire_dir = fire3(agent.get_location(), agent.get_direction(), opp.get_location(), opp.get_direction())
            actions.append(Action(agent_id, FIRE, fire_dir))
            shoot = True
            break
        for bullet in bullet_list:
            opp_fire_direction = bullet.get_direction()
            danger_fire_direction = fire3(bullet.get_location(), bullet.get_direction(), agent.get_location(), agent.get_direction())
            if opp_fire_direction.get_angle() <= danger_fire_direction.get_angle()+2 and opp_fire_direction.get_angle() >= danger_fire_direction.get_angle()-2:
                actions.append(Action(agent_id, UPDATE_DIRECTION, turn_back(agent.get_direction())))
                shoot = True
                break
        if shoot:
            continue

        # update view direction / direction with some probabilty
        rand_val = random.uniform(0, 1)
        if rand_val < 0.5:
            type = UPDATE_DIRECTION
            current_direction = agent.get_direction()
            direction = current_direction + \
                    Point(random.uniform(-1, 1), random.uniform(-1, 1))
        elif rand_val < 0.55:
            type = UPDATE_DIRECTION
            current_direction = agent.get_direction()
            direction = find_center(safe_zone)
            direction.sub(agent.get_location())
        else:
            type = UPDATE_VIEW_DIRECTION
            current_direction = agent.get_view_direction()
            direction = turn_left(current_direction)

        actions.append(Action(agent_id, type, direction))
    # print(actions)
    return actions


if __name__ == '__main__':
    server_port = ENV_PORT
    server_host = ENV_HOST

    red_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    red_socket.settimeout(2)

    red_host = 'localhost'
    red_port = RED_PORT
    red_socket.bind((red_host, red_port))

    print("Red player is ready to receive messages...")
    while True:
        try:
            environment_message, addr = red_socket.recvfrom(65527)
        except:
            print("Environment Not Responding...Red Closed")
            red_socket.close()
            sys.exit(1)
        state = pickle.loads(environment_message)
        actions = tick(state)
        new_message = pickle.dumps(actions)
        red_socket.sendto(new_message, (server_host, server_port))
