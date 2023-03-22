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
theta = math.asin(0.2) # 11 degrees

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
    if alpha + theta >= beta and alpha - theta <= beta:
        return direct_fire(blue_location, red_location)
    elif alpha > beta:
        return right_fire(blue_location, red_location)
    else:
        return left_fire(blue_location, red_location)

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
        agent_id = alert.agent_id
        agent = state.agents[agent_id]
        dire = agent.get_direction()
        type = None
        action = None
        if alert.alert_type == COLLISION:
            # reversed direction
            newDire = Point(0, 0)
            newDire.sub(dire)
            action = Action(agent_id, UPDATE_DIRECTION, newDire)
            agents_actions[agent_id].append((action, 0))
            # pass

        elif alert.alert_type == ZONE:
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
            pass
        elif alert.alert_type == DEAD:
            # dead players can be used as sheild against enemy bullets
            pass

    # object sighting triggered actions
    for Viewer_id in state.object_in_sight:

        if Viewer_id in agents_actions.keys():
            # viewer is agent

            Objects = state.object_in_sight[Viewer_id]
            Opponents = Objects.get('Agents')
            Bullets = Objects.get('Bullets')

            for Opponent in Opponents:
                # print(Opponent)
                # opp_dir = Opponent.get_direction()
                # opp_loc = Opponent.get_location()

                pass
                # print(Opponent.get_direction())

            for Bullet in Bullets:
                # print(Bullet)
                pass
                # print(Bullet.get_location())
    for opp in Enemy_locations:
        # find nearest agents
        # print(Enemy_locations[opp])
        for agent_id in state.agents:
            agent = state.agents[agent_id]
            dire = Enemy_locations.get(opp)[0]
            # Adire = agent.get_location()

            # dire.x = dire.x - Adire.x
            # dire.y = dire.y - Adire.y
            # dire.sub(agent.get_location())
            # dire.make_unit_magnitude()
            # print(dire)
            # dire.x=-dire.x
            # dire.y=-dire.y
            dire = fire(agent.get_location(),agent.get_direction(),Enemy_locations.get(opp)[0],Enemy_locations.get(opp)[1])

            action = Action(agent_id, FIRE, dire)
            agents_actions[agent_id].append((action, 0))

    final_actions = []
    for agent in agents_actions:
        actions = agents_actions[agent]
        agentobj = state.agents[agent]
        bestAction = Action(agent, UPDATE_DIRECTION, Point(1, 0))
        # if state.agents[agent].can_fire():
        #     bestAction = Action(agent, FIRE, Point(
        #         random.uniform(-1, 1), random.uniform(-1, 1)))
        # else:
        Sumx = 0
        Sumy = 0
        for point in Safe_Zone:
            Sumx += point.x
            Sumy += point.y
        Sumx /= 4
        Sumy /= 4
        newDire = Point(Sumx, Sumy)
        newDire.sub(state.agents[agent].get_location())
        # print(newDire)
        dirr = Point(random.uniform(-1,1),random.uniform(-1,1))
        dirr.make_unit_magnitude()
        # bestAction = Action(agent, UPDATE_DIRECTION, newDire)
        bestAction = Action(agent, UPDATE_VIEW_DIRECTION, turn_left(agentobj.get_view_direction()))
        for action in actions:
            bestAction = action[0]  # update best action
        # final_actions.append[bestAction] # uncomment it to see print statements
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
