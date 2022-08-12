from fileinput import filename
import os
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str, default=None)

def main(args):
    res = {'Trajectory_num': 0, 'Transition_num': 0, 'Total_episode_return': 0, 'Average_episode_return': 0,
           'Average_episode_trans': 0}
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
                    res[key] += float(content[key])
                files2remove.append(file)

    res['Average_episode_return'] = res['Total_episode_return'] / res['Trajectory_num']
    res['Average_episode_trans'] = res['Transition_num'] / res['Trajectory_num']
    res['Trajectory_num'] = int(res['Trajectory_num'])
    res['Transition_num'] = int(res['Transition_num'])
    res_json = json.dumps(res)
    with open(os.path.join(parent, '0_0_readme.json'), 'w') as file:
        file.write(res_json)
    for file in files2remove:
        os.remove(os.path.join(parent, file))


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
