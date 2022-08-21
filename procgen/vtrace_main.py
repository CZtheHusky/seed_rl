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


"""V-trace (IMPALA) binary for DeepMind Lab.

Actor and learner are in the same binary so that all flags are shared.
"""


from seed_rl.agents.vtrace import learner
from absl import app
from absl import flags
from seed_rl.procgen import env
from seed_rl.procgen import vtrace_networks
from seed_rl.common import actor
from seed_rl.common import common_flags  
import tensorflow as tf
import os

FLAGS = flags.FLAGS

# Optimizer settings.
flags.DEFINE_float('learning_rate', 0.00051866995608948655, 'Learning rate.')
flags.DEFINE_float('adam_epsilon', .000000003125, 'Adam epsilon.')
flags.DEFINE_float('rms_epsilon', .1, 'RMS epsilon.')
flags.DEFINE_float('rms_momentum', 0., 'RMS momentum.')
flags.DEFINE_float('rms_decay', .99, 'RMS decay.')
flags.DEFINE_string('sub_task', 'all', 'sub tasks, i.e. dmlab30, dmlab26, all, others')
flags.DEFINE_list('task_names', [], 'names of tasks')
flags.DEFINE_list('action_set', [], 'default action set')
flags.DEFINE_float('reward_threshold', 0., 'reward threshold for sampling')
flags.DEFINE_bool('extra_input', False, 'with or without the string input')

# Training.
flags.DEFINE_integer('save_checkpoint_secs', 900,
                     'Checkpoint save period in seconds.')
flags.DEFINE_integer('total_environment_frames', int(8e8),
                     'Total environment frames to train for.')
flags.DEFINE_integer('batch_size', 64, 'Batch size for training.')
flags.DEFINE_integer('inference_batch_size', -1,
                     'Batch size for inference, -1 for auto-tune.')
flags.DEFINE_integer('unroll_length', 100, 'Unroll length in 1agent steps.')
flags.DEFINE_integer('num_training_tpus', 1, 'Number of TPUs for training.')
flags.DEFINE_string('init_checkpoint', None, 'Path to the checkpoint used to initialize the agent.')
# flags.DEFINE_string('init_checkpoint', '../procgen_ckpt/fruitbot/ckpt-11', 'Path to the checkpoint used to initialize the agent.')


# Loss settings.
flags.DEFINE_float('entropy_cost', 0.033391318945337044, 'Entropy cost/multiplier.')
flags.DEFINE_float('target_entropy', None, 'If not None, the entropy cost is '
                   'automatically adjusted to reach the desired entropy level.')
flags.DEFINE_float('entropy_cost_adjustment_speed', 10., 'Controls how fast '
                   'the entropy cost coefficient is adjusted.')
flags.DEFINE_float('baseline_cost', .5, 'Baseline cost/multiplier.')
flags.DEFINE_float('kl_cost', 0., 'KL(old_policy|new_policy) loss multiplier.')
flags.DEFINE_float('discounting', .99, 'Discounting factor.')
flags.DEFINE_float('lambda_', .95, 'Lambda.')
flags.DEFINE_float('max_abs_reward', 0.,
                   'Maximum absolute reward when calculating loss.'
                   'Use 0. to disable clipping.')
flags.DEFINE_float('clip_norm', 0, 'We clip gradient norm to this value.')

# Logging
flags.DEFINE_integer('log_batch_frequency', 100, 'We average that many batches '
                     'before logging batch statistics like entropy.')
flags.DEFINE_integer('log_episode_frequency', 500, 'We average that many episodes'
                     ' before logging average episode return and length.')

def create_agent(action_space, unused_env_observation_space,
                 unused_parametric_action_distribution, extra_input):
    print('creating ImpalaDeep')
    return vtrace_networks.ImpalaDeep(action_space.n)


def create_optimizer(final_iteration):
  learning_rate_fn = tf.keras.optimizers.schedules.PolynomialDecay(
      FLAGS.learning_rate, final_iteration, 0)
  # optimizer = tf.keras.optimizers.Adam(learning_rate_fn, beta_1=0, epsilon=FLAGS.adam_epsilon)
  optimizer = tf.keras.optimizers.Adam(learning_rate_fn, beta_1=0)
  # optimizer = tf.keras.optimizers.RMSprop(learning_rate_fn, FLAGS.rms_decay, FLAGS.rms_momentum,
  #                                      FLAGS.rms_epsilon)
  return optimizer, learning_rate_fn


def main(argv):
  FLAGS.task_names = [FLAGS.sub_task]
  print(FLAGS.task_names)
  print(FLAGS.sub_task)
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')
  if FLAGS.run_mode == 'actor':
    actor.actor_loop(env.create_environment)
  elif FLAGS.run_mode == 'learner':
    learner.learner_loop(env.create_environment,
                         create_agent,
                         create_optimizer)
  else:
    raise ValueError('Unsupported run mode {}'.format(FLAGS.run_mode))


if __name__ == '__main__':
  gpus = tf.config.experimental.list_physical_devices('GPU')
  if gpus:
      tf.config.experimental.set_memory_growth(gpus[0], True)
  app.run(main)
