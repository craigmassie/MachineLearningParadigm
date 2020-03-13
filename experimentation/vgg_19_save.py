import tensorflow as tf

def export():
    model = tf.keras.applications.VGG19(weights='imagenet', include_top=True, input_tensor=tf.keras.Input(shape=(32, 32, 3)))
    model.compile(loss='categorical_crossentropy',
                        optimizer='rmsprop',
                        metrics=['accuracy'])
    model.save("vgg193.h5")

export()