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


from absl import app
from absl import flags

from seed_rl.agents.vtrace import sampler
from seed_rl.common import sampler_actor
from seed_rl.common import common_flags  
from seed_rl.dmlab import env
from seed_rl.dmlab import networks
import tensorflow as tf
from seed_rl.dmlab import games
import os
FLAGS = flags.FLAGS

# Optimizer settings.
flags.DEFINE_float('learning_rate', 0.00031866995608948655, 'Learning rate.')
# flags.DEFINE_float('adam_epsilon', 3.125e-7, 'Adam epsilon.')
flags.DEFINE_float('rms_epsilon', .1, 'RMS epsilon.')
flags.DEFINE_float('rms_momentum', 0., 'RMS momentum.')
flags.DEFINE_float('rms_decay', .99, 'RMS decay.')
flags.DEFINE_string('sub_task', 'all', 'sub tasks, i.e. dmlab30, dmlab26, all, others')
flags.DEFINE_list('task_names', [], 'names of tasks')
flags.DEFINE_list('action_set', [], 'default action set')

def create_agent(action_space, unused_env_observation_space,
                 unused_parametric_action_distribution):
  return networks.ImpalaDeep(action_space.n)


def create_optimizer(final_iteration):
  learning_rate_fn = tf.keras.optimizers.schedules.PolynomialDecay(
      FLAGS.learning_rate, final_iteration, 0)
  # optimizer = tf.keras.optimizers.Adam(learning_rate_fn, beta_1=0,
  #                                      epsilon=FLAGS.adam_epsilon)
  optimizer = tf.keras.optimizers.RMSprop(learning_rate_fn, FLAGS.rms_decay, FLAGS.rms_momentum,
                                       FLAGS.rms_epsilon)
  return optimizer, learning_rate_fn


def main(argv):
  FLAGS.action_set = env.DEFAULT_ACTION_SET
  if FLAGS.sub_task == 'dmlab30':
    FLAGS.task_names = games.DMLAB_30
  elif FLAGS.sub_task == 'others':
    FLAGS.task_names = games.OTHERS
  elif FLAGS.sub_task == 'dmlab26':
    FLAGS.task_names = games.DMLAB_26
  else:
    FLAGS.task_names = [FLAGS.sub_task]
  print('task')
  print(FLAGS.sub_task)
  print('subtask names')
  print(FLAGS.task_names)
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')
  if FLAGS.run_mode == 'actor':
    sampler_actor.actor_loop(env.create_environment)
  elif FLAGS.run_mode == 'learner':
    for i in range(len(FLAGS.task_names)):
      cur_path = FLAGS.logdir + '/' + FLAGS.task_names[i] + '_dataset'
      if not os.path.exists(cur_path):
        os.makedirs(cur_path)
    sampler.learner_loop(env.create_environment,
                         create_agent,
                         create_optimizer)
  else:
    raise ValueError('Unsupported run mode {}'.format(FLAGS.run_mode))


if __name__ == '__main__':
  app.run(main)