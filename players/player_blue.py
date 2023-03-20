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
            if Enemy_locations.get(id)==None:
                Enemy_locations[id] = [loc,dire]

        for Bullet in Bullets:
            id = Bullet._id
            dire = Bullet.get_direction()
            loc = Bullet.get_location()
            if Enemy_bullets.get(id)==None:
                Enemy_bullets[id] = [loc,dire]


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
        if alert.alert_type == COLLISION:
            pass
        elif alert.alert_type == ZONE:
            pass
        elif alert.alert_type == BULLET_HIT:
            pass
        elif alert.alert_type == DEAD:
            #dead players can be used as sheild against enemy bullets
            pass

    # object sighting triggered actions
    for Viewer_id in state.object_in_sight:
        
        if Viewer_id in agents_actions.keys():
            # viewer is agent
            Objects = state.object_in_sight[Viewer_id]
            Opponents = Objects.get('Agents')
            Bullets = Objects.get('Bullets')

            for Opponent in Opponents:
                pass
                # print(Opponent.get_direction())

            for Bullet in Bullets:
                pass
                # print(Bullet.get_location())

    final_actions = []
    for agent in agents_actions:
        actions = agents_actions[agent]
        bestAction = Action(agent, UPDATE_DIRECTION,Point(1, 0))

        for action in actions:
            bestAction = Action(agent, UPDATE_DIRECTION,Point(1, 0))  # update best action
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
