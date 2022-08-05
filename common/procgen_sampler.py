# coding=utf-8
# Copyright 2019 The SEED Authors
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""SEED actor."""

import os
import timeit

from absl import flags
from absl import logging
import numpy as np
from seed_rl import grpc
from seed_rl.common import common_flags  
from seed_rl.common import env_wrappers
from seed_rl.common import profiling
from seed_rl.common import utils
import tensorflow as tf
import h5py

def reset_data():
    return {'observations': [],
            'actions': [],
            'terminals': [],
            'timeouts': [],
            'rewards': [],
            'infos/prev_level_seed': [],
            'infos/prev_level_complete': [],
            'infos/level_seed': [],
            }

def append_data(data, obs, act, rew, infos1, infos2, infos3, done):
    data['observations'].extend(obs)
    data['actions'].extend(act)
    data['rewards'].extend(rew)
    data['terminals'].extend(done)
    data['timeouts'].extend(done)
    data['infos/prev_level_seed'].extend(infos1)
    data['infos/prev_level_complete'].extend(infos2)
    data['infos/level_seed'].extend(infos3)


def npify(data):
    for k in data:
        if k in ['terminals', 'timeouts']:
            dtype = np.bool_
            data[k] = np.array(data[k], dtype=dtype)
        else:
            data[k] = np.array(data[k])

FLAGS = flags.FLAGS

flags.DEFINE_integer('task', 0, 'Task id.')
flags.DEFINE_integer('num_actors_with_summaries', 4,
                     'Number of actors that will log debug/profiling TF '
                     'summaries.')
flags.DEFINE_bool('render', False,
                  'Whether the first actor should render the environment.')
flags.DEFINE_integer('save_interval', int(1e3), 'save interval')
flags.DEFINE_integer('save_num', 10, 'save num')


def are_summaries_enabled():
  return FLAGS.task < FLAGS.num_actors_with_summaries


def actor_loop(create_env_fn, config=None, log_period=30):
  """Main actor loop.

  Args:
    create_env_fn: Callable (taking the task ID as argument) that must return a
      newly created environment.
    config: Configuration of the training.
    log_period: How often to log in seconds.
  """
  if not config:
    config = FLAGS
  save_idx = 0
  total_transitions = 0
  total_eps = 0
  cur_trans_num = 0
  cur_ep_num = 0
  avg_ep_reward = 0
  actor_idx = FLAGS.task
  env_batch_size = FLAGS.env_batch_size
  # dummy_infos = np.array(0, dtype=np.uint8)
  logging.info('Starting actor loop. Task: %r. Environment batch size: %r',
               FLAGS.task, env_batch_size)
  is_rendering_enabled = FLAGS.render and FLAGS.task == 0
  if are_summaries_enabled():
    summary_writer = tf.summary.create_file_writer(
        os.path.join(FLAGS.logdir, 'actor_{}'.format(FLAGS.task)),
        flush_millis=20000, max_queue=1000)
    timer_cls = profiling.ExportingTimer
  else:
    summary_writer = tf.summary.create_noop_writer()
    timer_cls = utils.nullcontext
  
  obsBuffer = [[] for i in range(env_batch_size)]
  actionsBuffer = [[] for i in range(env_batch_size)]
  rewardBuffer = [[] for i in range(env_batch_size)]
  terminalBuffer = [[] for i in range(env_batch_size)]
  infos1Buffer = [[] for i in range(env_batch_size)]
  infos2Buffer = [[] for i in range(env_batch_size)]
  infos3Buffer = [[] for i in range(env_batch_size)]
  data2save = reset_data()
  actor_step = 0
  id_offset = FLAGS.task * env_batch_size
  env_id = [id_offset + i for i in range(env_batch_size)]
  env_id = np.array(env_id, np.int32)
  with summary_writer.as_default():
    while True:
      try:
        # Client to communicate with the learner.
        client = grpc.Client(FLAGS.server_address)
        utils.update_config(config, client)
        batched_env = create_env_fn(actor_idx, config)
        # env_wrappers.BatchedEnvironment(
        #     create_env_fn, env_batch_size, FLAGS.task * env_batch_size, config)

        # env_id = batched_env.env_ids
        run_id = np.random.randint(
            low=0,
            high=np.iinfo(np.int64).max,
            size=env_batch_size,
            dtype=np.int64)
        observation = batched_env.reset()
        reward = np.zeros(env_batch_size, np.float32)
        raw_reward = np.zeros(env_batch_size, np.float32)
        done = np.zeros(env_batch_size, np.bool)
        abandoned = np.zeros(env_batch_size, np.bool)
        global_step = 0
        episode_step = np.zeros(env_batch_size, np.int32)
        episode_return = np.zeros(env_batch_size, np.float32)
        episode_raw_return = np.zeros(env_batch_size, np.float32)
        episode_step_sum = 0
        episode_return_sum = 0
        episode_raw_return_sum = 0
        episodes_in_report = 0

        elapsed_inference_s_timer = timer_cls('actor/elapsed_inference_s', 1000)
        last_log_time = timeit.default_timer()
        last_global_step = 0
        while True:
          for i in range(env_batch_size):
            # print(i)
            # print(observation[i].shape)
            # print(observation[i])
            obsBuffer[i].append(observation['rgb'][i])
          tf.summary.experimental.set_step(actor_step)
          env_output = utils.EnvOutput(reward, done, observation['rgb'],
                                       abandoned, episode_step)
          with elapsed_inference_s_timer:
            action = client.inference(env_id, run_id, env_output, raw_reward)
          np_action = action.numpy()
          with timer_cls('actor/elapsed_env_step_s', 1000):
            observation, reward, done, info = batched_env.step(np_action)
          for i in range(env_batch_size):
            actionsBuffer[i].append(np_action[i])
            rewardBuffer[i].append(reward[i])
            terminalBuffer[i].append(done[i])
            # data['infos/prev_level_seed'].extend(infos1)
            # data['infos/prev_level_complete'].extend(infos2)
            # data['infos/level_seed'].extend(infos3)
            infos1Buffer[i].append(info[i]['prev_level_seed'])
            infos3Buffer[i].append(info[i]['prev_level_complete'])
            infos2Buffer[i].append(info[i]['level_seed'])
            episode_step[i] += 1
            episode_return[i] += reward[i]
            raw_reward[i] = float((info[i] or {}).get('score_reward',
                                                      reward[i]))
            episode_raw_return[i] += raw_reward[i]
            # If the info dict contains an entry abandoned=True and the
            # episode was ended (done=True), then we need to specially handle
            # the final transition as per the explanations below.
            abandoned[i] = (info[i] or {}).get('abandoned', False)
            assert done[i] if abandoned[i] else True
            if done[i]:
              # append_data(data, obs, act, rew, infos, done)
              # If the episode was abandoned, we need to report the final
              # transition including the final observation as if the episode has
              # not terminated yet. This way, learning algorithms can use the
              # transition for learning.
              if abandoned[i]:
                # We do not signal yet that the episode was abandoned. This will
                # happen for the transition from the terminal state to the
                # resetted state.
                assert env_batch_size == 1 and i == 0, (
                    'Mixing of batched and non-batched inference calls is not '
                    'yet supported')
                env_output = utils.EnvOutput(reward,
                                             np.array([False]), observation['rgb'],
                                             np.array([False]), episode_step)
                with elapsed_inference_s_timer:
                  # action is ignored
                  client.inference(env_id, run_id, env_output, raw_reward)
                reward[i] = 0.0
                raw_reward[i] = 0.0

              # Periodically log statistics.
              current_time = timeit.default_timer()
              episode_step_sum += episode_step[i]
              episode_return_sum += episode_return[i]
              episode_raw_return_sum += episode_raw_return[i]
              global_step += episode_step[i]
              episodes_in_report += 1

              if episode_raw_return[i] >= FLAGS.reward_threshold:
                cur_trans_num += episode_step[i]
                cur_ep_num += 1
                avg_ep_reward += episode_raw_return[i]
                append_data(data2save, obsBuffer[i], actionsBuffer[i], rewardBuffer[i], infos1Buffer[i], infos2Buffer[i], infos3Buffer[i], terminalBuffer[i])
                total_eps += 1
              actionsBuffer[i] = []
              obsBuffer[i] = []
              rewardBuffer[i] = []
              terminalBuffer[i] = []
              infos1Buffer[i] = []
              infos3Buffer[i] = []
              infos2Buffer[i] = []
              if cur_trans_num >= FLAGS.save_interval:
                total_transitions += cur_trans_num
                logging.info(f'saving data, save idx: {save_idx} env idx: {actor_idx} cur transitions: {cur_trans_num} tt transitions: {total_transitions} episodes: {cur_ep_num}')
                dataset2save = h5py.File(FLAGS.logdir + '/' + FLAGS.task_names[actor_idx % len(FLAGS.task_names)] + '_dataset/' + str(actor_idx) + '_' + str(save_idx) + '.hdf5', 'w')
                save_idx += 1
                cur_trans_num = 0
                cur_ep_num = 0
                npify(data2save)
                for k in data2save:
                    dataset2save.create_dataset(k, data=data2save[k], compression='gzip')
                data2save = reset_data()

              if current_time - last_log_time >= log_period:
                logging.info(
                    'Actor steps: %i, Return: %f Raw return: %f '
                    'Episode steps: %f, Speed: %f steps/s', global_step,
                    episode_return_sum / episodes_in_report,
                    episode_raw_return_sum / episodes_in_report,
                    episode_step_sum / episodes_in_report,
                    (global_step - last_global_step) /
                    (current_time - last_log_time))
                last_global_step = global_step
                episode_return_sum = 0
                episode_raw_return_sum = 0
                episode_step_sum = 0
                episodes_in_report = 0
                last_log_time = current_time

              episode_step[i] = 0
              episode_return[i] = 0
              episode_raw_return[i] = 0

          # Finally, we reset the episode which will report the transition
          # from the terminal state to the resetted state in the next loop
          # iteration (with zero rewards).
          # with timer_cls('actor/elapsed_env_reset_s', 10):
          #   observation = batched_env.reset_if_done(done)

          actor_step += 1
      except (tf.errors.UnavailableError, tf.errors.CancelledError):
        logging.info(f'saving data, save idx: {save_idx} env idx: {actor_idx} cur transitions: {cur_trans_num} tt transitions: {total_transitions} episodes: {cur_ep_num}')
        dataset2save = h5py.File(FLAGS.logdir + '/dataset/' + str(actor_idx) + '_' + str(save_idx) + '.hdf5', 'w')
        npify(data2save)
        for k in data2save:
            dataset2save.create_dataset(k, data=data2save[k], compression='gzip')
        logging.info(f'actor terminated, env idx: {actor_idx}, total saves: {save_idx} total transitions: {total_transitions} total episodes: {total_eps} avg ep return: {avg_ep_reward/total_eps}')
        logging.info('Inference call failed. This is normal at the end of '
                     'training.')
        batched_env.close()
