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
# additional imports
from models.Agent import Agent


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
    # for 10 deg left rotations
    # curr_dir = Point(curr_dir.x, curr_dir.y)
    # an = curr_dir.get_angle()
    # an += 10
    # curr_dir = Point(math.cos(math.radians(an)), math.sin(math.radians(an)))
    # return curr_dir


def turn_right(curr_dir: Point) -> Point:
    return Point(curr_dir.y, -curr_dir.x)
    
def turn_back(curr_dir: Point) -> Point:
    return Point(-curr_dir.x, -curr_dir.y)

# fire
# red is opponent
theta = math.asin(0.1) # 11 degrees

def direct_fire(blue_location: Point, red_location: Point) -> Point:
    return Point(red_location.x - blue_location.x, red_location.y - blue_location.y)

def left_fire(blue_location: Point, red_location: Point) -> Point: 
    v = direct_fire(blue_location, red_location)
    xx = v.x * math.cos(theta) - v.y * math.sin(theta)
    yy = v.x * math.sin(theta) + v.y * math.cos(theta)
    return Point(xx, yy)

def right_fire(blue_location: Point, red_location: Point) -> Point:
    v = direct_fire(blue_location, red_location)
    xx = v.x * math.cos(-theta) - v.y * math.sin(-theta)
    yy = v.x * math.sin(-theta) + v.y * math.cos(-theta)
    return Point(xx, yy)
    

def fire(blue_location: Point, blue_direction: Point, red_location: Point, red_direction: Point) -> Point:
    alpha = direct_fire(blue_location, red_location).get_angle()
    rel = red_direction
    rel.sub(blue_direction)
    red_direction = rel
    beta = Point(red_direction.x - direct_fire(blue_location, red_location).x, red_direction.y - direct_fire(blue_location, red_location).y).get_angle()
    if alpha + 15 >= beta and alpha - 15 <= beta:
        return direct_fire(blue_location, red_location)
    elif alpha > beta:
        return right_fire(blue_location, red_location)
    else:
        return left_fire(blue_location, red_location)


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


def friend_not_in_line(fire_direction: Point, agent: Agent, other: List[Agent]) -> bool:
    fire_direction = fire_direction.get_angle()
    for friend in other:
        diff_vector = friend.get_location()
        diff_vector.sub(agent.get_location())
        diff_vector = diff_vector.get_angle()
        # 10 deg diff or distance is more than 50
        if ((abs(fire_direction - diff_vector)) < 10) and (friend.get_location().distance(agent.get_location()) < 60):
            return False
    return True


def tick(state: State) -> List[Action]:

    Team = state.team
    Time = state.time
    Obstacles = state.obstacles
    Zone = state.zone
    Safe_Zone = state.safe_zone
    Is_Zone_Shinking = state.is_zone_shrinking

    Enemy_locations = {}
    Enemy_bullets = {}
    for Viewer_id in state.object_in_sight:
        Objects = state.object_in_sight[Viewer_id]
        Opponents = Objects.get('Agents')
        Bullets = Objects.get('Bullets')

        for Opponent in Opponents:
            id = Opponent._id
            dire = Opponent.get_direction()
            loc = Opponent.get_location()
            if Enemy_locations.get(id) == None:
                Enemy_locations[id] = [loc, dire]

        for Bullet in Bullets:
            id = Bullet._id
            dire = Bullet.get_direction()
            loc = Bullet.get_location()
            if Enemy_bullets.get(id) == None:
                Enemy_bullets[id] = [loc, dire]

    agents_actions = {}

    """
    multiple actions for all agent, 
    each action is associated with a priority which represents how beneficial that action is,
    at last most priority actions are more likely to happen   
    """

    # initialization for agents_actions
    for agent_id in state.agents:
        agents_actions[agent_id] = [] 

    # alert triggered actions
    for alert in state.alerts:
        # print(alert.alert_type) # no alert of type ZONE or BULLET_HIT
        agent_id = alert.agent_id
        agent = state.agents[agent_id]
        dire = agent.get_direction()
        if alert.alert_type == COLLISION:
            # reversed direction
            # newDire = Point(0, 0)
            # newDire.sub(dire)
            # left direction
            p = random.uniform(0, 1)
            if p < 0.3:
                newDire = turn_left(dire)
            elif p < 0.6:
                newDire = turn_right(dire)
            else:
                newDire = turn_back(dire)
            action = Action(agent_id, UPDATE_DIRECTION, newDire)
            agents_actions[agent_id].append((action, 0))
            # pass

        elif alert.alert_type == ZONE:
            # no such alert
            Sumx = 0
            Sumy = 0
            for point in Safe_Zone:
                Sumx += point.x
                Sumy += point.y
            Sumx /= 4
            Sumy /= 4
            newDire = Point(Sumx, Sumy)
            newDire.sub(agent.get_location())
            # newDire=normalize new direction point
            action = Action(agent_id, UPDATE_DIRECTION, newDire)
            agents_actions[agent_id].append((action, 0))

        elif alert.alert_type == BULLET_HIT:
            # no such alert
            pass
        elif alert.alert_type == DEAD:
            # dead players can be used as sheild against enemy bullets or finding probable enemy locations
            pass

    # object sighting triggered actions
    for Viewer_id in state.object_in_sight:

        # viewer is agent
        Objects = state.object_in_sight[Viewer_id]
        Opponents = Objects.get('Agents')
        Bullets = Objects.get('Bullets')

        agent = state.agents[Viewer_id]                      # viewer
        agents = [state.agents[agt] for agt in state.agents]  # friends
        for agt in agents:
            if agt.agent_id == agent.agent_id:
                agents.remove(agt)
                break

        for Opponent in Opponents:
            opp_dir = Opponent.get_direction()
            opp_loc = Opponent.get_location()
            fdirr = fire(agent.get_location(),
                         agent.get_direction(), opp_loc, opp_dir)
            if friend_not_in_line(fdirr, agent, agents):
                action = Action(Viewer_id, FIRE, fdirr)
                agents_actions[Viewer_id].append((action, 0))

        for Bullet in Bullets:
            # update_direction/fire action acc to bullet direction and location
            pass
        
        # update zone directions
        # zone_var = zone_check(agent.get_location(),agent.get_direction(),Safe_Zone)
        # dir_change = zone_var[1]
        # if dir_change:
        #     action = Action (agent.id(),UPDATE_DIRECTION,zone_var[0])
        #     agents_actions[Viewer_id].append((action,0))

    final_actions = []
    for agent_id in agents_actions:
        agent = state.agents[agent_id]
        # bestAction = Action(agent, UPDATE_DIRECTION, Point(1, 0)) # -->> move left only
        bestAction = Action(agent_id, UPDATE_VIEW_DIRECTION, turn_left(agent.get_view_direction()))  # -->> default turn_left action
        ZoneCheck = zone_check(agent.get_location(),agent.get_direction(),Safe_Zone)
        if ZoneCheck[1]:
            agents_actions[agent_id].append((Action(agent_id,UPDATE_DIRECTION,ZoneCheck[0]),0))
        actions = agents_actions[agent_id]
        for action in actions:
            bestAction = action[0]  # update to last added action
        final_actions.append(bestAction)

    return final_actions


if __name__ == '__main__':
    server_port = ENV_PORT
    server_host = 'localhost'

    blue_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    blue_socket.settimeout(2)

    blue_host = 'localhost'
    blue_port = BLUE_PORT
    blue_socket.bind((blue_host, blue_port))
    print("Blue player is ready to receive messages...")
    while True:
        try:
            environment_message, addr = blue_socket.recvfrom(65527)
        except:
            print("Environment Not Responding...Blue Closed")
            blue_socket.close()
            sys.exit(1)
        state = pickle.loads(environment_message)
        actions = tick(state)
        new_message = pickle.dumps(actions)
        blue_socket.sendto(new_message, (server_host, server_port))
