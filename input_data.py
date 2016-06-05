import tensorflow as tf
import numpy as np
import datetime

def weight_variable(shape):
  initial = tf.random_normal(shape, stddev=0.1)
  return tf.Variable(initial)

def bias_variable(shape):
  initial = tf.constant(0.1, shape=shape)
  return tf.Variable(initial)

def model(X, weights_conv, bias_conv, weights_fc, bias_fc):

    # INPUT X [32x32x3] will hold the raw pixel values of the image,
    # in this case an image of width 32, height 32, and with three color channels R,G,B.

    # CONV layer will compute the output of neurons that are connected to local regions in the input,
    # each computing a dot product between their weights and a small region they are connected to in the input volume.
    # This may result in volume such as [32x32x32] if we decide to use 32 filters.
    conv = tf.nn.conv2d(X, weights_conv, strides=[1, 1, 1, 1], padding='SAME') + bias_conv

    # RELU layer will apply an elementwise activation function, such as the max(0,x)max(0,x) thresholding at zero.
    # This leaves the size of the volume unchanged ([32x32x32]).
    activations = tf.nn.relu(conv)  # activations shape=(32, 32, 32)
    print "conv&relu shape:", activations.get_shape()

    # POOL layer will perform a downsampling operation along the spatial dimensions (width, height),
    # resulting in volume such as [16x16x32].
    pool = tf.nn.max_pool(activations, ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1], padding='SAME') # -> 16, 16, 32
    print "pool shape:", pool.get_shape()

    # TODO: second fully connected layer with dropout?
    # could add additional fully connected layer + dropout here (e.g with 1024 neurons, like in MNIST tutorial:
    # https://www.tensorflow.org/versions/r0.8/tutorials/mnist/pros/index.html)
    # pool_flat = tf.reshape(pool, [-1, 16*16*32]) # flatten result of pooling
    # activations_fc0 = tf.nn.relu(tf.matmul(pool_flat, weights_fc) + bias_fc)

    # FC (i.e. fully-connected) layer will compute the class scores, resulting in volume of size [1x1x10],
    # where each of the 10 numbers correspond to a class score, such as among the 10 categories of CIFAR-10.
    pool = tf.reshape(pool, [-1, weights_fc.get_shape().as_list()[0]]) # flatten to fit fc layer
    mul = tf.matmul(pool, weights_fc)

    #return tf.nn.softmax(mul + bias_fc) -> NO! perform softmax when computing cross entropy instead (see below)

    return mul + bias_fc # is this correct? no idea :(

def get_batch(number):
    data = unpickle('cifar-10/data_batch_%d' % number)
    return data['data'], dense_to_one_hot(data['labels'])

def get_test():
    data = unpickle('cifar-10/test_batch')
    return data['data'], dense_to_one_hot(data['labels'])

def unpickle(file):
    import cPickle
    fo = open(file, 'rb')
    dict = cPickle.load(fo)
    fo.close()
    return dict

def dense_to_one_hot(labels_dense, num_classes=10):
    """Convert class labels from scalars to one-hot vectors."""
    num_labels = len(labels_dense)
    labels_dense = np.array(labels_dense, dtype=np.uint8)
    index_offset = np.arange(num_labels) * num_classes
    labels_one_hot = np.zeros((num_labels, num_classes), dtype=np.uint8)
    labels_one_hot.flat[index_offset + labels_dense.ravel()] = 1
    return labels_one_hot

# input vector 32x32x3 image
X = tf.placeholder(tf.float32, [None, 32, 32, 3]) # input
Y = tf.placeholder(tf.float32, [None, 10]) # output (10 classes)

num_features = 32
batch_size = 128
test_size = 256

weights_conv = weight_variable([3, 3, 3, num_features]) # 3x3 convolution, 3 input channels, 32 features=output channels
bias_conv = bias_variable([num_features]) # bias variable for each feature=output channel

weights_fc = weight_variable([16 * 16 * num_features, 10]) # output of pooling -> fully connected layer with 10 output neurons
bias_fc = bias_variable([10]) # bias for every output neuron

py_x = model(X, weights_conv, bias_conv, weights_fc, bias_fc)

cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(py_x, Y))
train_op = tf.train.AdamOptimizer(1e-4).minimize(cost)
predict_op = tf.argmax(py_x, 1)

correct_prediction = tf.equal(tf.argmax(py_x, 1), tf.argmax(Y, 1))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

trX, trY = get_batch(1) # training
teX, teY = get_test() # test

trX = trX.reshape(-1, 32, 32, 3)  # 32x32x3 input img
teX = teX.reshape(-1, 32, 32, 3)  # 32x32x3 input img

with tf.Session() as sess:

    tf.initialize_all_variables().run()

    print "Training started at: ", datetime.datetime.now().time()

    for i in range(100):
        training_batch = zip(range(0, len(trX), batch_size),
                             range(batch_size, len(trX), batch_size))
        for start, end in training_batch:
            batch_labels = trY[start:end] #  shape = (128, 32, 32, 3)
            batch_samples = trX[start:end] # shape = (128, 10)

            sess.run(train_op, feed_dict={X: batch_samples, Y: batch_labels})

        test_indices = np.arange(len(teX))  # Get A Test Batch
        np.random.shuffle(test_indices)
        test_indices = test_indices[0:test_size]

        print(i, np.mean(np.argmax(teY[test_indices], axis=1) ==
                         sess.run(predict_op, feed_dict={X: teX[test_indices],
                                                         Y: teY[test_indices]})))

    print "Training finished at: ", datetime.datetime.now().time()