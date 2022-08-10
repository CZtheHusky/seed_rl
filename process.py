import os
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str, default=None)

def main(args):
    res = {'Trajectory num': 0, 'Transition num': 0, 'Total episode return': 0, 'Average episode return': 0,
           'Average episode trans': 0}
    parent = args.path
    file_list = os.listdir(parent)
    for file in file_list:
        if os.path.isfile(os.path.join(parent, file)):
            fileName, suffix = file.split('.')
            if suffix == 'txt':
                print(file)
                with open(os.path.join(parent, file), 'r') as f:
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        key, value = line.split(':')
                        value = float(value)
                        res[key] += value
                os.remove(os.path.join(parent, file))

    res['Average episode return'] = res['Total episode return'] / res['Trajectory num']
    res['Average episode trans'] = res['Transition num'] / res['Trajectory num']
    res['Transition num'] = int(res['Transition num'])
    res['Trajectory num'] = int(res['Trajectory num'])
    res_json = json.dumps(res)
    with open(os.path.join(parent, 'readme.json'), 'w') as file:
        file.write(res_json)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
