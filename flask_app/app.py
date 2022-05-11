from flask import Flask, flash, request, jsonify, render_template
import tensorflow as tf

def create_preproc_image(filename):
    preproc = _Preprocessor()
    img = preproc.read_from_jpegfile(filename)
    return preproc.preprocess(img)


class _Preprocessor:
    def __init__(self):
        # nothing to initialize
        pass

    def read_from_tfr(self, proto):
        feature_description = {
            'image': tf.io.VarLenFeature(tf.float32),
            'shape': tf.io.VarLenFeature(tf.int64),
            'label': tf.io.FixedLenFeature([], tf.string, default_value=''),
            'label_int': tf.io.FixedLenFeature([], tf.int64, default_value=0),
        }
        rec = tf.io.parse_single_example(
            proto, feature_description
        )
        shape = tf.sparse.to_dense(rec['shape'])
        img = tf.reshape(tf.sparse.to_dense(rec['image']), shape)
        label_int = rec['label_int']
        return img, label_int

    def read_from_jpegfile(self, filename):
        img = tf.io.read_file(filename)
        img = tf.image.decode_jpeg(img, channels=IMG_CHANNELS)
        img = tf.image.convert_image_dtype(img, tf.float32)
        return img

    def preprocess(self, img):
        return tf.image.resize_with_pad(img, IMG_HEIGHT, IMG_WIDTH)

serving_model = tf.keras.models.load_model("ClothingPredictionModel")

categories = ["T-Shirt", "Longsleeve", "Pants", "Shoes", "Shirt", "Dress", "Outwear", "Shorts", "Hat", "Skirt"]
IMG_HEIGHT = 224
IMG_WIDTH = 224
IMG_CHANNELS = 3

flask_app = Flask(__name__)

@flask_app.route("/")
def Home():
    return render_template("index.html")

@flask_app.route("/predict", methods = ["POST"])
def predict():
    filename = "static/images/" + request.form["file"]
    img = create_preproc_image(filename)
    batch_image = tf.reshape(img, [1, IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS])
    batch_pred = serving_model.predict(batch_image)
    pred = batch_pred[0]
    pred_label_index = tf.math.argmax(pred).numpy()
    pred_label = categories[pred_label_index]
    prob = pred[pred_label_index]
    prob_round=round(prob*100)

    return render_template("index.html", prediction_text="Drabužių kategorija yra  {} su tikimybe {}%"
                           .format(pred_label, prob_round), image_file=filename)

@flask_app.route("/test")
def test_ok():
    return {"result": "ok"}

if __name__ == "__main__":
    flask_app.run(debug=True)



