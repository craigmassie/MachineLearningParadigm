from flask import Flask, request, abort
from flask_restful import Resource, Api
import json
import tensorflow as tf
from tensorflow.keras.datasets import cifar10
'''TODO: remove all preprocessing to seperate API'''
from sklearn.model_selection import train_test_split

app = Flask(__name__)
api = Api(app)
batch_size = 128
num_classes = 10
epochs = 12

def request_key_exists(d, request_key):
    try:
        request_value = d[request_key]
    except KeyError:
        app.logger.error(f"'{request_key}' key not found in request body. Unable to find begin training.")
        abort(400)
    return request_value

def get_image_shape(dataset_location):
    '''TODO'''
    return (28, 28, 1)


@app.route('/trainModel', methods=['POST'])
def post():
    '''
    TODO: Fix this terrible model and generalise. Functionality does work however.
    '''
    # d = request.get_json()
    # model_location, dataset_location = request_key_exists(d, "model_location"), request_key_exists(d, "dataset_location")
    image_shape = tf.keras.layers.Input(shape=(32, 32, 3))
    
    vgg_model = tf.keras.applications.VGG19(weights='imagenet', include_top=False, input_tensor=image_shape)
    vgg_layers = dict([(layer.name, layer) for layer in vgg_model.layers])
    (x_train, y_train), (x_test, y_test) = cifar10.load_data()
    y_train = tf.keras.utils.to_categorical(y_train, num_classes)
    y_test = tf.keras.utils.to_categorical(y_test, num_classes)

    '''Source code taken from https://riptutorial.com/keras/example/32608/transfer-learning-using-keras-and-vgg'''

    # Getting output tensor of the last VGG layer that we want to include
    input_layer = vgg_layers['block2_pool'].output

    # Stacking a new simple convolutional network on top of it    
    x = tf.keras.layers.Conv2D(filters=64, kernel_size=(3, 3), activation='relu')(input_layer)
    x = tf.keras.layers.MaxPooling2D(pool_size=(2, 2))(x)
    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dense(256, activation='relu')(x)
    x = tf.keras.layers.Dropout(0.5)(x)
    x = tf.keras.layers.Dense(10, activation='softmax')(x)

    custom_model = tf.keras.Model(inputs=vgg_model.input, outputs=x)

    # Make sure that the pre-trained bottom layers are not trainable
    for layer in custom_model.layers[:7]:
        layer.trainable = False
    app.logger.info(custom_model.summary())
    # Do not forget to compile it
    custom_model.compile(loss='categorical_crossentropy',
                        optimizer='rmsprop',
                        metrics=['accuracy'])

    custom_model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          verbose=1,
          validation_data=(x_test, y_test))
    score = custom_model.evaluate(x_test, y_test, verbose=0)
    return('Test loss:', score[0], 'Test accuracy:', score[1])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    