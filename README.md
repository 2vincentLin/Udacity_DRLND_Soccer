[//]: # (Image References)

[image1]: https://raw.githubusercontent.com/Unity-Technologies/ml-agents/master/docs/images/soccer.png "Soccer"


# Udacity DRLND soccer 

### Introduction

This project implement [MADDPG](https://arxiv.org/abs/1706.02275) to solve 
[Soccer](https://github.com/Unity-Technologies/ml-agents/blob/master/docs/Learning-Environment-Examples.md#soccer-twos) 
environment.
![Soccer][image1]


- Set-up: Environment where four agents compete in a 2 vs 2 toy soccer game.
- Goal:  
    - Striker: Get the ball into the opponent's goal.
    - Goalie: Prevent the ball from entering its own goal.
- Agents: The environment contains four agents, with two linked to one Brain (strikers) and two linked to another (goalies).
- Agent Reward Function (dependent):  
    - Striker:  
        - +1 When ball enters opponent's goal.  
        - -0.1 When ball enters own team's goal.  
        - -0.001 Existential penalty.
    - Goalie:  
        - -1 When ball enters team's goal.
        - +0.1 When ball enters opponents goal.
        - +0.001 Existential bonus.
- Brains: Two Brain with the following observation/action space:
    - Vector Observation space: 112 corresponding to local 14 ray casts, each detecting 7 possible object types,
    along with the object's distance. Perception is in 180 degree view from front of agent.
    - Vector Action space: (Discrete) One Branch
        - Striker: 6 actions corresponding to forward, backward, sideways movement, as well as rotation.
        - Goalie: 4 actions corresponding to forward, backward, sideways movement.
    - Visual Observations: None.
- Reset Parameters: None
- Benchmark Mean Reward (Striker & Goalie Brain): 0 (the means will be inverse of each other and criss crosses 
during training)


### Download the environment

1. Download the environment from one of the links below.  You need only select the environment that matches your 
operating system:
    - Linux: [click here](https://s3-us-west-1.amazonaws.com/udacity-drlnd/P3/Soccer/Soccer_Linux.zip)
    - Mac OSX: [click here](https://s3-us-west-1.amazonaws.com/udacity-drlnd/P3/Soccer/Soccer.app.zip)
    - Windows (32-bit): [click here](https://s3-us-west-1.amazonaws.com/udacity-drlnd/P3/Soccer/Soccer_Windows_x86.zip)
    - Windows (64-bit): [click here](https://s3-us-west-1.amazonaws.com/udacity-drlnd/P3/Soccer/Soccer_Windows_x86_64.zip)

2. Place the file in the same directory as Soccer.ipynb 

