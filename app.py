from flask import Flask, send_from_directory
from werkzeug.utils import secure_filename
from flask import jsonify, request
import jwt
from functools import wraps

from models import *

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hnf4567Gbjalkjemcd64dvFDda'
user = Users(name='admin', password='pwd')

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

SET = Settings(mode_clean)


def token_required(f):
    '''
    to verify token
    :param f:
    :return:
    '''

    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 403

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])

        except Exception as ex:
            return jsonify({'message': 'Token is invalid!'}), 403

        return f(*args, **kwargs)

    return decorated


@app.route('/api/login')
def login():
    '''
    to generate token
    :return: json: {"token": "JKV1Q.."}
    '''

    token = jwt.encode({'user': user.name}, app.config['SECRET_KEY'])

    return jsonify({'token': token.decode('UTF-8')})


@app.route('/api/input', methods=['POST', 'GET'])
@token_required
def in_calc_out():
    '''
    main function:
    input: file ('.pdf', '.jpeg', '.jpg', '.bmp', '.png') + token (from /api/login),
    :return: json :{"polygons": [{"1": [[1271, 1485], [1185, 1485], .. ]}
    in debug mode: figure with identified rooms
    '''

    # remove all old files
    delete_all()

    if app.debug:
        set = Settings(mode_save_files)  # save and return figure with identified rooms

        # remove out file (figure with identified rooms)
        # os.remove(os.path.join(SET.out_folder_img_coord, out_Coord_file_mk(img_file_name)))

    resp_upload, img_file_name = upload_file()

    try:
        contors = FindCount(SET, img_file_name)
        resp = contors.json_out

    except Exception as ex:
        resp = jsonify({'message': 'Error in calculations'})
        resp.status_code = 400

    # remove input img file
    os.remove(os.path.join(SET.UPLOAD_FOLDER, img_file_name))

    if app.debug:
        # return out file (figure with identified rooms)
        try:
            coord_fig_file = out_coord_file_mk(img_file_name)

            return send_from_directory(SET.out_folder_img_coord, coord_fig_file)
            # return resp

        except Exception as ex:
            resp = jsonify({'message': 'Error in out figure (figure with identified rooms)'})
            resp.status_code = 400
            return resp

    else:
        return resp


##########

@app.route('/api/upload', methods=['POST'])
@token_required
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        resp = jsonify({'message': 'No file part in the request'})
        resp.status_code = 400
        return resp, ''

    file = request.files['file']
    if file.filename == '':
        resp = jsonify({'message': 'No file selected for uploading'})
        resp.status_code = 400
        return resp, ''

    if not file and allowed_file(file.filename, SET):
        resp = jsonify({'message': 'Allowed file types are pdf, jpeg, jpg, bmp, png'})
        resp.status_code = 400
        return resp, ''

    else:
        filename = secure_filename(file.filename)
        file.save(os.path.join(SET.UPLOAD_FOLDER, filename))
        resp = jsonify({'message': 'File successfully uploaded', 'filename': filename})
        resp.status_code = 201

        return resp, filename


@app.route('/files_list', methods=['GET'])
def files_list():
    try:
        list_in_files = create_list_of_files_in_formats(SET.out_folder_img_coord)
        return jsonify(list_in_files)

    except Exception as ex:
        return jsonify({'message': 'Can not find folder for input files: see SET.out_folder_img_coord'})


@app.route('/out/coord', methods=['POST'])
def output_coord(filename):
    return send_from_directory(SET.out_folder_img_coord, filename), 200


@app.route('/delete_all', methods=['POST'])
@token_required
def delete_all():
    try:
        list_in_files = create_list_of_files_in_formats(SET.out_folder_img_coord)
    except Exception as ex:
        return jsonify({'message': 'Can not find folder for input files: see SET.out_folder_img_coord'})

    if len(list_in_files) > 0:
        for filename in list_in_files:

            try:
                os.remove(os.path.join(SET.out_folder_img_coord, filename))
            except Exception as ex:
                pass

    return jsonify({'message': 'files were removed'})


if __name__ == '__main__':
    app.run(debug=True)
