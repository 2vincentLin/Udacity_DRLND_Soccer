

## action

this project needs two different agents, one for goalie, another for striker. 
goalie has 4 discrete actions, striker has 6 discrete actions. when output actions, use 
the following code(the eps is from DQN network, should not used here)

```python
def act(self, state, eps=0.0):
    '''
    get actions
    '''
    state = torch.from_numpy(state).float().unsqueeze(0).to(device)
    self.qnetwork_local.eval()
    with torch.no_grad():
        action = self.qnetwork_local(state)
    self.qnetwork_local.train()

    if np.random.random() > eps:
        return np.argmax(action.cpu().data.numpy())
    else:
        return np.random.choice(np.arange(self.action_size))

```

## agent

- maddpg.Agent() should have name attribute because it'll have two agents, when saving 
weights, it'll overwrite each other.
- Maybe I should put goalie and striker on the same team into one agent.