
import tensorflow as tf
from tensorflow.contrib import layers
from tensorflow.contrib.framework import arg_scope

class SphereFace(object):
  def __init__(self, weight_decay=0.0005,  name='SphereFace'):
    self.num_outputs=[64, 128, 256, 512]

    self.weight_decay = weight_decay

    self.name = name

  def prelu(self, x, name='prelu'):
    channel_axis = 3
    shape = [1, 1, 1, 1]
    shape[channel_axis] = x.get_shape().as_list()[channel_axis]

    alpha = tf.get_variable('alpha', shape,
                            initializer=tf.constant_initializer(0.25),
                            dtype=tf.float32)
    return tf.nn.relu(x) + alpha*(x-tf.abs(x))*0.5

  def resBlock(self, x, num_outputs, scope=None):
    with tf.variable_scope(scope, 'resBlock'):
      shortcut = x
      x = layers.conv2d(x, num_outputs, kernel_size=3, biases_initializer=None, weights_initializer=tf.truncated_normal_initializer(0.0, 0.01))      
      x = layers.conv2d(x, num_outputs, kernel_size=3, biases_initializer=None, weights_initializer=tf.truncated_normal_initializer(0.0, 0.01))
      x += shortcut

    return x

  def __call__(self, inputs, is_training=False, reuse=None):
    with tf.variable_scope(self.name, reuse=reuse):
        with arg_scope([layers.conv2d], activation_fn=self.prelu, 
                                        weights_regularizer=layers.l2_regularizer(self.weight_decay)):

          inputs = tf.transpose(inputs, [0,1, 2,3])
          print("inputs.shape is : {}".format(inputs.shape))
          with tf.variable_scope('conv1'):
            net = layers.conv2d(inputs, num_outputs=self.num_outputs[0], kernel_size=3, stride=2)
            net = self.resBlock(net, num_outputs=self.num_outputs[0])
            

          with tf.variable_scope('conv2'):
            net = layers.conv2d(net, num_outputs=self.num_outputs[1], kernel_size=3, stride=2)
            net = layers.repeat(net, 2, self.resBlock, self.num_outputs[1]) 

          with tf.variable_scope('conv3'):
            net = layers.conv2d(net, num_outputs=self.num_outputs[2], kernel_size=3, stride=2)
            net = layers.repeat(net, 4, self.resBlock, self.num_outputs[2])

          with tf.variable_scope('conv4'):
            net = layers.conv2d(net, num_outputs=self.num_outputs[3], kernel_size=3, stride=2)
            net = self.resBlock(net, num_outputs=self.num_outputs[3]) 

          net = tf.reshape(net, [-1, net.get_shape().as_list()[1]*net.get_shape().as_list()[2]*net.get_shape().as_list()[3]])
            
          net = layers.fully_connected(net, num_outputs=512, activation_fn=None, 
                    weights_regularizer=layers.l2_regularizer(self.weight_decay)) # 512

    return net

  @property
  def vars(self):
    return tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.name)
