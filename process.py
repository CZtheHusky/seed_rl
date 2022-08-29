from fileinput import filename
import os
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str, default=None)

def main(args):
    res = {'Trajectory_num': 0, 'Transition_num': 0, 'Total_episode_return': 0, 'Average_episode_return': 0,
           'Average_episode_trans': 0, 'Max_ep_reward': -1e9, 'Min_ep_reward': 1e9, 'Max_ep_length': -1e9, 'Min_ep_length': 1e9}
    parent = args.path
    file_list = os.listdir(parent)
    files2remove = []
    for file in file_list:
        if os.path.isfile(os.path.join(parent, file)):
            fileName, suffix = file.split('.')
            if suffix == 'json' and fileName != '0_0_readme':
                print(file)
                with open(os.path.join(parent, file), 'r') as f:
                    content = json.load(f)
                for key in res.keys():
                    if key not in ['Max_ep_reward', 'Min_ep_reward']:
                        res[key] += float(content[key])
                res['Max_ep_reward'] = max(res['Max_ep_reward'], content['Max_ep_reward'])
                res['Min_ep_reward'] = min(res['Min_ep_reward'], content['Min_ep_reward'])
                res['Max_ep_length'] = max(res['Max_ep_length'], content['Max_ep_length'])
                res['Min_ep_length'] = min(res['Min_ep_length'], content['Min_ep_length'])
                files2remove.append(file)

    res['Average_episode_return'] = res['Total_episode_return'] / res['Trajectory_num']
    res['Average_episode_trans'] = res['Transition_num'] / res['Trajectory_num']
    res['Trajectory_num'] = int(res['Trajectory_num'])
    res['Transition_num'] = int(res['Transition_num'])
    res['Min_ep_reward'] = float(res['Min_ep_reward'])
    res['Max_ep_reward'] = float(res['Max_ep_reward'])
    res['Min_ep_length'] = int(res['Min_ep_length'])
    res['Max_ep_length'] = int(res['Max_ep_length'])
    res_json = json.dumps(res)
    with open(os.path.join(parent, '0_0_readme.json'), 'w') as file:
        file.write(res_json)
    # for file in files2remove:
    #     os.remove(os.path.join(parent, file))


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
