from concurrent.futures import ThreadPoolExecutor
import numpy as np
import random
import copy
from collections import namedtuple, deque

from model import Actor, Critic

import torch
import torch.nn.functional as F
import torch.optim as optim

BUFFER_SIZE = int(1e6)  # replay buffer size
BATCH_SIZE = 2  # minibatch size
GAMMA = 0.999  # discount factor
TAU = 1e-3  # for soft update of target parameters
LR_ACTOR = 1e-4  # learning rate of the actor
LR_CRITIC = 1e-4  # learning rate of the critic
WEIGHT_DECAY = 0.0001  # L2 weight decay

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


# device = torch.device("cpu")

torch.set_printoptions(threshold=np.inf)


class Agent():
    def __init__(self, state_size, full_state_size, action_size, num_agents, num_process, name, random_seed=0.0):
        self.state_size = state_size
        self.action_size = action_size
        self.num_agents = num_agents
        self.num_process = num_process
        self.name = name
        self.full_state_size = full_state_size
        self.full_action_size = num_agents

        torch.manual_seed(random_seed)

        self.agents = [base_agent(state_size, action_size, self.full_state_size, self.full_action_size, random_seed) for
                       _ in range(num_agents)]
        self.memory = ReplayBuffer(BUFFER_SIZE, BATCH_SIZE, random_seed)

    def act(self, states):
        return [self.agents[i].act(states[i]) for i in range(self.num_agents)]

    def step(self, states, actions, rewards, next_states, dones):
        """Save experience in replay memory, and use random sample from buffer to learn."""
        # Save experience / reward
        for i in range(self.num_agents):
            self.memory.add(states, actions, rewards, next_states, dones)

        # Learn, if enough samples are available in memory
        if len(self.memory) > BATCH_SIZE:
            for i in range(self.num_agents):
                experiences = self.memory.sample()
                self.learn(experiences, i, GAMMA)
        # if len(self.memory) > BATCH_SIZE:
        #     with ThreadPoolExecutor(max_workers=self.num_process) as executor:
        #         for i in range(self.num_agents):
        #             experiences = self.memory.sample()
        #             executor.submit(self.learn, experiences, i, GAMMA)

    def target_act(self, states):
        '''

        :param states: tensor shape (batch size * self.num_agents, action_size)
        :return: tensor shape (batch size * self.num_agents, action_size)
        '''
        next_states = [states[i::self.num_agents] for i in range(self.num_agents)]
        target_actions = [self.agents[i].target_act(next_states[i]) for i in range(self.num_agents)]
        return torch.cat(target_actions)

    def local_act(self, states, i):
        """


        :param states:
        :param i:
        :return:
        """
        states = [states[i::self.num_agents] for i in range(self.num_agents)]
        local_actions = [self.agents[j].actor_local(states[j]) if j == i
                         else self.agents[j].actor_local(states[j]).detach()
                         for j in range(self.num_agents)]
        return torch.cat(local_actions)

    def learn(self, experiences, i, gamma):
        """Update policy and value parameters using given batch of experience tuples.
        Q_targets = r + γ * critic_target(next_state, actor_target(next_state))
        where:
            actor_target(state) -> action
            critic_target(state, action) -> Q-value
        Params
        ======
            experiences (Tuple[torch.Tensor]): tuple of (s, a, r, s', done) tuples
            gamma (float): discount factor
        """
        states, actions, rewards, next_states, dones = experiences

        full_states = states.view(-1, self.full_state_size)
        full_actions = actions.view(-1, self.full_action_size)
        full_next_states = next_states.view(-1, self.full_state_size)

        states_i = states[i::self.num_agents]
        rewards_i = rewards[:, i].view(-1, 1)
        actions_i = actions[i::self.num_agents]
        dones_i = dones[:, i].view(-1, 1)
        # print('full  ', actions, '\n', 'one {}'.format(i), actions_i)

        # print('states shape\t', states.shape)
        # print('states_{}_shape\t'.format(i), states_i.shape)
        # print('next states shape\t', next_states.shape)
        # print('actions shape\t', actions.shape)
        # print('actions_{}_shape\t'.format(i), actions_i.shape)
        # print('rewards shape\t', rewards.shape)
        # print('rewards_{}_shape\t'.format(i), rewards_i.shape)
        # print('dones shape\t', dones.shape)
        # print('dones_{} shape\t'.format(i), dones_i.shape)
        # print('full states shape\t', full_states.shape)
        # print('full actions shape\t', full_actions.shape)
        #
        # print('rewards ', rewards)
        # print('rewards i ', rewards_i)

        # ---------------------------- update critic ---------------------------- #
        # Get predicted next-state actions and Q values from target models
        full_actions_next = self.target_act(next_states)
        full_actions_next = full_actions_next.view(-1, self.full_action_size)  # need to change shape for critic
        # print('full_actions_next shape ', full_actions_next.shape)
        with torch.no_grad():
            Q_targets_next = self.agents[i].critic_target(full_next_states, full_actions_next)

        # y = reward[agent_number].view(-1, 1) + self.discount_factor * q_next * (1 - done[agent_number].view(-1, 1))
        # Compute Q targets for current states (y_i)
        Q_targets = rewards_i + (gamma * Q_targets_next * (1 - dones_i))
        # Compute critic loss
        Q_expected = self.agents[i].critic_local(full_states, full_actions)
        critic_loss = F.mse_loss(Q_expected, Q_targets)
        # print('critic loss ', critic_loss)
        # Minimize the loss
        self.agents[i].critic_optimizer.zero_grad()
        critic_loss.backward()
        self.agents[i].critic_optimizer.step()

        # ---------------------------- update actor ---------------------------- #
        # Compute actor loss
        actions_pred = self.local_act(states, i)

        print('before ', actions_pred)

        actions_pred = actions_pred.view(-1, self.full_action_size)
        print('after ', actions_pred)
        actor_loss = -self.agents[i].critic_local(full_states, actions_pred).mean()
        print('actor loss ', actor_loss)
        # Minimize the loss
        self.agents[i].actor_optimizer.zero_grad()
        actor_loss.backward()
        self.agents[i].actor_optimizer.step()

        # ----------------------- update target networks ----------------------- #
        self.agents[i].soft_update(self.agents[i].critic_local, self.agents[i].critic_target, TAU)
        self.agents[i].soft_update(self.agents[i].actor_local, self.agents[i].actor_target, TAU)

        # print('end ')

    def reset(self):
        for i in range(self.num_agents):
            self.agents[i].reset()

    def save_weights(self):
        for i in range(self.num_agents):
            torch.save(self.agents[i].actor_local.state_dict(), 'model_weights/{}_agent{}_actor_local.pth'.format(self.name, i))
            torch.save(self.agents[i].critic_local.state_dict(), 'model_weights/{}_agent{}_critic_local.pth'.format(self.name, i))
            torch.save(self.agents[i].actor_target.state_dict(), 'model_weights/{}_agent{}_actor_target.pth'.format(self.name, i))
            torch.save(self.agents[i].critic_target.state_dict(), 'model_weights/{}_agent{}_critic_target.pth'.format(self.name, i))

    def load_weights(self):
        if torch.cuda.is_available():
            for i in range(self.num_agents):
                self.agents[i].actor_local.load_state_dict(
                    torch.load('model_weights/{}_agent{}_actor_local.pth'.format(self.name, i)))
                self.agents[i].critic_local.load_state_dict(
                    torch.load('model_weights/{}_agent{}_critic_local.pth'.format(self.name, i)))
                self.agents[i].actor_target.load_state_dict(
                    torch.load('model_weights/{}_agent{}_actor_target.pth'.format(self.name, i)))
                self.agents[i].critic_target.load_state_dict(
                    torch.load('model_weights/{}_agent{}_critic_target.pth'.format(self.name, i)))
        else:
            for i in range(self.num_agents):
                self.agents[i].actor_local.load_state_dict(
                    torch.load('{}_mode_weights/agent{}_actor_local.pth'.format(self.name, i), map_location='cpu'))
                self.agents[i].critic_local.load_state_dict(
                    torch.load('{}_mode_weights/agent{}_critic_local.pth'.format(self.name, i), map_location='cpu'))
                self.agents[i].actor_target.load_state_dict(
                    torch.load('{}_mode_weights/agent{}_actor_target.pth'.format(self.name, i), map_location='cpu'))
                self.agents[i].critic_target.load_state_dict(
                    torch.load('{}_mode_weights/agent{}_critic_target.pth'.format(self.name, i), map_location='cpu'))


class base_agent():
    def __init__(self, state_size, action_size, full_state_size, full_action_size, random_seed):
        """

        :param state_size: dimension of state for actor
        :param action_size: dimension of action for actor
        :param full_state_size: dimension of full state for critic
        :param full_action_size: dimension of full action for critic
        :param random_seed: seed for noise
        """
        self.state_size = state_size
        self.action_size = action_size

        # Actor Network (w/ Target Network)
        self.actor_local = Actor(state_size, action_size).to(device)
        self.actor_target = Actor(state_size, action_size).to(device)
        self.actor_optimizer = optim.Adam(self.actor_local.parameters(), lr=LR_ACTOR)

        # Critic Network (w/ Target Network)
        self.critic_local = Critic(full_state_size, full_action_size).to(device)
        self.critic_target = Critic(full_state_size, full_action_size).to(device)
        self.critic_optimizer = optim.Adam(self.critic_local.parameters(), lr=LR_CRITIC, weight_decay=WEIGHT_DECAY)

        # add hard copy
        self.hard_copy(self.actor_local, self.actor_target)
        self.hard_copy(self.critic_local, self.critic_target)

        # Noise process
        self.noise = OUNoise(action_size, random_seed)

    def act(self, state):
        """Returns actions for given state as per current policy."""
        state = torch.from_numpy(state).float().unsqueeze(0).to(device)
        self.actor_local.eval()
        with torch.no_grad():
            action = self.actor_local(state).cpu().data.numpy()
        self.actor_local.train()

        return np.argmax(action)

    def target_act(self, state):
        """Returns actions for given state as per current policy."""
        self.actor_target.eval()
        with torch.no_grad():
            action = self.actor_target(state)
        self.actor_target.train()

        return np.argmax(action)

    def reset(self):
        self.noise.reset()

    def soft_update(self, local_model, target_model, tau):
        """Soft update model parameters.
        θ_target = τ*θ_local + (1 - τ)*θ_target

        Params
        ======
            local_model: PyTorch model (weights will be copied from)
            target_model: PyTorch model (weights will be copied to)
            tau (float): interpolation parameter
        """
        for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
            target_param.data.copy_(tau * local_param.data + (1.0 - tau) * target_param.data)

    def hard_copy(self, local_model, target_model):

        for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
            target_param.data.copy_(local_param.data)


class ReplayBuffer:
    """Fixed-size buffer to store experience tuples."""

    def __init__(self, buffer_size, batch_size, seed):
        """Initialize a ReplayBuffer object.
        Params
        ======
            buffer_size (int): maximum size of buffer
            batch_size (int): size of each training batch
        """
        self.memory = deque(maxlen=buffer_size)  # internal memory (deque)
        self.batch_size = batch_size
        self.experience = namedtuple("Experience", field_names=["state", "action", "reward", "next_state", "done"])
        self.seed = random.seed(seed)

    def add(self, state, action, reward, next_state, done):
        """Add a new experience to memory."""
        e = self.experience(state, action, reward, next_state, done)
        self.memory.append(e)

    def sample(self):
        """Randomly sample a batch of experiences from memory."""
        experiences = random.sample(self.memory, k=self.batch_size)

        states = torch.from_numpy(np.vstack([e.state for e in experiences if e is not None])).float().to(device)
        actions = torch.from_numpy(np.vstack([e.action for e in experiences if e is not None])).float().to(device)
        rewards = torch.from_numpy(np.vstack([e.reward for e in experiences if e is not None])).float().to(device)
        next_states = torch.from_numpy(np.vstack([e.next_state for e in experiences if e is not None])).float().to(
            device)
        dones = torch.from_numpy(np.vstack([e.done for e in experiences if e is not None]).astype(np.uint8)).float().to(
            device)

        return (states, actions, rewards, next_states, dones)

    def __len__(self):
        """Return the current size of internal memory."""
        return len(self.memory)


class OUNoise:
    """Ornstein-Uhlenbeck process."""

    def __init__(self, size, seed, mu=0., theta=0.15, sigma=0.1):
        """Initialize parameters and noise process."""
        self.mu = mu * np.ones(size)
        self.theta = theta
        self.sigma = sigma
        self.seed = random.seed(seed)
        self.reset()

    def reset(self):
        """Reset the internal state (= noise) to mean (mu)."""
        self.state = copy.copy(self.mu)

    def sample(self):
        """Update internal state and return it as a noise sample."""
        x = self.state
        #         print('state before sample ', self.state)
        dx = self.theta * (self.mu - x) + self.sigma * np.array([random.random() for i in range(len(x))])
        self.state = x + dx
        #         print('state after sample ', self.state)
        return self.state
