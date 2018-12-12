'''
This script is to help you stop training anytime you want or check how is training going.


'''



import pickle

log_path = 'log.pkl'


def print_log():
    with open(log_path, 'rb') as f:
        print(pickle.load(f))


def end_now():
    with open(log_path, 'rb') as f:
        log = pickle.load(f)

    log['end_now'] = True

    with open(log_path, 'wb') as f:
        pickle.dump(log, f)


def modify_log():
    with open(log_path, 'rb') as f:
        log = pickle.load(f)

    

    # log = {
    #     'total_episodes': 120,
    #     'current_episodes': 0,
    #     'scores': [],
    #     'save_every': 30,
    #     'print_every': 30,
    #     'end_now': False,
    #     'solved': False,
    #     'solved_score': 30,
    #     'solve_in_episodes': None
    # }
    with open(log_path, 'wb') as f:
        pickle.dump(log, f)


if __name__ == '__main__':
    print_log()
