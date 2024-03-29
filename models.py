import numpy as np
import cv2
import fitz  # PyMuPDF is installed
import os
import json
import pathlib

# list_of_img_formats = ['.pdf', '.jpeg', '.jpg', '.bmp', '.png', '.dwg']
list_of_img_formats = ['.pdf', '.jpeg', '.jpg', '.bmp', '.png']


class Users(object):
    def __init__(self, name, password):
        self.name = name
        self.password = password


mode_clean = {'save_out_img_noCoord': False,
              'save_out_img_Coord': False,
              'show_conturs': False,  # show img with conturs
              'show_process': False,  # show the process of adding the rooms corner coordinates
              'save_json_in_file': False,
              'UPLOAD_FOLDER': 'Input_img/',
              'ALLOWED_EXTENSIONS': {'pdf', 'jpeg', 'jpg', 'bmp', 'png'},
              'OUT_FOLDER_MAIN': 'Out/',
              'OUT_FOLDER_NoCoord': 'Out_img_noCoord/',
              'OUT_FOLDER_Coord': 'Out_img_Coord/',
              'OUT_FOLDER_json': 'Out_json/',
              'in_files': [],  #
              'noise_removal_threshold': 7000,  # minimal area of a room in pix ~5000-10000
              'k_approxPolyDP': 0.02  # koeff for approxPolyDP procedure ~0.02
              }

mode_save_files = {'save_out_img_noCoord': False,
                   'save_out_img_Coord': True,
                   'show_conturs': False,  # show img with conturs
                   'show_process': False,  # show the process of adding the rooms corner coordinates
                   'save_json_in_file': False,
                   'UPLOAD_FOLDER': 'Input_img/',
                   'ALLOWED_EXTENSIONS': {'pdf', 'jpeg', 'jpg', 'bmp', 'png'},
                   'OUT_FOLDER_MAIN': 'Out/',
                   'OUT_FOLDER_NoCoord': 'Out_img_noCoord/',
                   'OUT_FOLDER_Coord': 'Out_img_Coord/',
                   'OUT_FOLDER_json': 'Out_json/',
                   'in_files': [],  #
                   'noise_removal_threshold': 7000,  # minimal area of a room in pix ~5000-10000
                   'k_approxPolyDP': 0.02  # koeff for approxPolyDP procedure ~0.02
                   }


class Settings(object):
    '''
    set settings
    '''

    def __init__(self, mode):
        self.mode = mode

        # folder for input (JPEG/JPG, BMP, PDF, PNG, DWG) files
        self.input_img_folder_rel = self.mode['UPLOAD_FOLDER']
        # folder for output files
        self.out_folder_main_rel = self.mode['OUT_FOLDER_MAIN']

        self.ALLOWED_EXTENSIONS = mode['ALLOWED_EXTENSIONS']

        self.UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.input_img_folder_rel)

        self.input_img_folder = path_abs_make(self.input_img_folder_rel)
        self.out_folder_main = path_abs_make(self.out_folder_main_rel)

        # out image no coordinates
        self.out_folder_img_noCoord = os.path.join(self.out_folder_main, self.mode['OUT_FOLDER_NoCoord'])
        # out image with coordinates
        self.out_folder_img_coord = os.path.join(self.out_folder_main, self.mode['OUT_FOLDER_Coord'])
        # out json
        self.out_folder_json = os.path.join(self.out_folder_main, self.mode['OUT_FOLDER_json'])

        if mode['in_files'] != 'all':
            # make a list of '.pdf', '.jpeg', '.jpg', '.bmp', '.png' files
            self.in_files = create_list_of_files_in_formats(self.input_img_folder)
            # self.in_files = create_list_of_pdf(self.input_img_folder) #.pdf only

        else:

            self.in_files = mode['in_files']

        self.save_out_img_noCoord = self.mode['save_out_img_noCoord']
        self.save_out_img_Coord = self.mode['save_out_img_Coord']
        self.show_conturs = self.mode['show_conturs']
        self.show_process = self.mode['show_process']
        self.save_json_in_file = self.mode['save_json_in_file']

        # minimal area of a room in pix
        self.noise_removal_threshold = self.mode['noise_removal_threshold']
        self.k_approxPolyDP = self.mode['k_approxPolyDP']


def allowed_file(filename, set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in set.ALLOWED_EXTENSIONS


def out_json_file_mk(img_file_name):
    return '%s.json' % (replce_format_from_file_name(img_file_name))


def out_no_coord_file_mk(img_file_name):
    prefix = 'in'
    return '%s_%s.jpg' % (prefix, replce_format_from_file_name(img_file_name))


def out_coord_file_mk(img_file_name):
    prefix = 'rooms'
    return '%s_%s.jpg' % (prefix, replce_format_from_file_name(img_file_name))


class FindCount():
    def __init__(self, set, img_file_name):
        '''

        :param img_file_name: .pdf or .png
        :param out_folder_name:
        '''
        # input files
        self.input_img_folder = set.input_img_folder
        self.img_file_name = img_file_name  # image .pdf file

        # output files
        self.out_folder_img_noCoord = set.out_folder_img_noCoord  # out image no coordinates
        self.out_folder_img_coord = set.out_folder_img_coord  # out image with coordinates
        # out json
        self.out_folder_json = set.out_folder_json
        # self.out_json_file = '%s.txt' % (replce_format_from_file_name(self.img_file_name))
        self.out_json_file = out_json_file_mk(self.img_file_name)
        self.out_json_file_full = '%s%s' % (self.out_folder_json, self.out_json_file)
        # out figures
        self.save_out_img_noCoord = set.save_out_img_noCoord
        self.save_out_img_Coord = set.save_out_img_Coord
        self.show_conturs = set.show_conturs
        self.show_process = set.show_process
        self.save_json_in_file = set.save_json_in_file

        # paramerers for the contour approximation (smoothing)
        self.k_approxPolyDP = set.k_approxPolyDP

        # minimal area of a room in pix
        self.noise_removal_threshold = set.noise_removal_threshold

        # read image (.pdf or .jpeg/.jpg, .bmp, .png)
        self.img_rgb = load_image(self.input_img_folder + self.img_file_name)

        # an image transformation to make it easier to find contours
        self.img_go = image_transform2find_contours(self.img_rgb)

        # to find rooms on a figure using cv2.findContours
        self.corner_coordinates = self.find_rooms(self.noise_removal_threshold, self.show_conturs)

        # Out:
        # return json
        # self.json_out = json.dumps(self.corner_coordinates, cls=NumpyEncoder, sort_keys=True)
        json1 = {'polygons': [{key: item} for key, item in self.corner_coordinates.items()]}
        self.json_out = json.dumps(json1, cls=NumpyEncoder, sort_keys=True)

        # save json
        if self.save_json_in_file:
            save_out_dict(self.corner_coordinates, self.out_json_file_full)

        # save the input image to file
        self.out_noCoord_file = out_no_coord_file_mk(self.img_file_name)
        if self.save_out_img_noCoord:
            save_test_image(self.out_folder_img_noCoord, self.out_noCoord_file, self.img_rgb)

        # save figure  with coordinates
        self.out_Coord_file = out_coord_file_mk(self.img_file_name)
        if self.save_out_img_Coord:
            draw_main_out_figure(self.img_rgb, self.corner_coordinates,
                                 self.out_folder_img_coord, self.out_Coord_file,
                                 self.show_process)

    def find_rooms(self, noise_removal_threshold, show_conturs):
        '''
        to find rooms on a figure using cv2.findContours
        : param noise_removal_threshold - minimal area of a room in pix (~5000)
        :return:
        '''

        # find the contours
        contours, hierarchy = cv2.findContours(self.img_go, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        # find the contours 'bigger' then the minimal area in pixel (see noise_removal_threshold)
        contours = choose_big_conturs(contours, noise_removal_threshold)

        # approximate (smooth) the contour and to return as dictionary:
        # {N_room: [[x1, y1], [x2, y2],..], ..}
        corner_coordinates, contours_smooth = return_contours_as_poligon(contours.copy(),
                                                                         self.k_approxPolyDP)

        # sendbox figure for contours -->
        if show_conturs:
            draw_conturs(contours_smooth, self.img_rgb.copy(), True, False)

        return corner_coordinates


def for_all_pdf_files_in_list(set):
    '''
    :param set:
    :return:
    '''

    # if there are files in the input folder
    if len(set.in_files) == 0:
        print('Tere is no files in the input folder')
        raise SystemExit(1)

    # for all files in SET.in_files list
    for img_file_name in set.in_files:
        print('In file: %s' % (img_file_name))
        contors = FindCount(set, img_file_name)


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def create_list_of_pdf(path):
    lst = os.listdir(path)
    return [x for x in lst if '.pdf' in x]


def create_list_of_files_in_formats(path):
    lst = os.listdir(path)

    out_list = []
    for file_name in lst:
        for img_format in list_of_img_formats:
            if img_format in file_name:
                out_list.append(file_name)

    return out_list


def create_list_of_img(path):
    lst = os.listdir(path)
    list_of_formats = ['.pdf']

    return [x for x in lst if '.pdf' in x]


def replce_format_from_file_name(file_name):
    for f in list_of_img_formats:
        file_name = file_name.replace(f, '')

    return file_name


def load_image(file_name):
    '''
    read image in .pdf or .png
    :param file_name:
    :return:
    '''
    # from library:
    if '.pdf' in file_name:
        return read_pdf(file_name)
    elif ('.jpeg' in file_name) or ('.jpg' in file_name) or ('.png' in file_name) or ('.bmp' in file_name):
        return cv2.imread(file_name)


def read_pdf(pdf_file_name):
    '''

    :param pdf_file_name:
    :param out_folder_name:
    :return:
    '''
    # pages = convert_from_path(pdf_file, dpi=200)[0]
    # pages.save('out.jpg', 'JPEG')

    doc = fitz.open(pdf_file_name)
    # split pages
    for i, page in enumerate(doc.pages()):
        # print(i)
        zoom = 1
        mat = fitz.Matrix(zoom, zoom)
        pix = page.getPixmap(matrix=mat)
        img_data = pix.getImageData('png')

    # save image from opencv
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    return img


def image_transform2find_contours(img):
    '''

    :param img:
    :return:
    '''
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_smoothed = cv2.GaussianBlur(gray, (3, 3), 0)

    # contour recognition
    edged = cv2.Canny(gray, 10, 250)

    # create and apply a closure
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

    # inversion to initial state (white background)
    out_img = cv2.bitwise_not(closed)

    return out_img


def save_test_image(out_folder_name, file_name, img):
    '''
    to ctrate a sendbox image
    :param out_folder_name:
    :param img_file_name:
    :param img:
    :param prefix:
    :return:
    '''

    full_file_name = out_folder_name + file_name

    cv2.imwrite(full_file_name, img)


def choose_big_conturs(contours, noise_removal_threshold):
    '''
    find the contours 'bigger' then the minimal area in pixel (see noise_removal_threshold)

    :param contours:
    :param noise_removal_threshold:
    :param show_fig:
    :param img:
    :return:
    '''
    max_area = 1000000

    contours2 = []
    for contour in contours:
        area = cv2.contourArea(contour)

        if (area > noise_removal_threshold) and (area < max_area):
            contours2.append(contour)

    return contours2


def draw_conturs(contours, img, draw_img, save_img):
    '''

    :param contours:
    :param img:
    :param draw_img:
    :param save_img:
    :return:
    '''

    total = 0
    for c in contours:
        # contour tops > 2
        if len(c) > 2:
            cv2.drawContours(img, [c], -1, (0, 0, 255), 4)
            total += 1

    # sowing the output image
    print('Здесь %i комнат' % total)
    if draw_img:
        image_show(img)

    if save_img:
        cv2.imwrite('output_p.jpg', img)


def image_show(image):
    '''

    :param image:
    :return:
    '''
    cv2.imshow("Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def return_contours_as_poligon(contours, k_approx_poly_dp):
    '''
    to smooth the contour and
    to save contours to dictionary with coordinates
    {N_room : [[x1, y1], [x2, y2], ..], ..}
    :param contours:
    :param img:
    :return: {1: array([[1271, 1313], .. [1271, 1485]], 2: ..}
    '''
    # k_approxPolyDP = 0.02

    i_cont = 0
    corner_coordinates, contours_out = {}, []
    for contur in contours:
        i_cont += 1

        # approximate (smooth) the contour
        peri = cv2.arcLength(contur, True)
        approx_contur = cv2.approxPolyDP(contur, k_approx_poly_dp * peri, True)

        # apply Convex Hull
        hull_contur = cv2.convexHull(approx_contur)

        corner_coordinates.update({i_cont: [xx[0] for xx in hull_contur]})
        contours_out.append(approx_contur)

    return corner_coordinates, contours_out


def draw_main_out_figure(img, corner_coordinates, out_folder_name, file_name, show_process):
    '''
    :return:
    '''

    for i_room, contur in corner_coordinates.items():
        cont_color = (np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255))

        show_img_with_dots_from_conturs(img, contur, i_room, cont_color, show_process)

    # file_name = 'Coord.jpg'
    cv2.imwrite('%s%s' % (out_folder_name, file_name), img)


def show_img_with_dots_from_conturs(img, contur, i_cont, color, showing_img):
    '''
    out figure with patterns locations we found
    :param img:
    :param list_of_cord: [[1271 1313], [1212 1314], ..  [1271 1485]]
    :return:
    '''
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Radius of circle, Blue color in BGR, Line thickness of -1 px
    radius, thickness = 10, 5
    font_scale, fontthickness = 1, 2  # fontScale

    for coordinate in contur:
        # center coordinates and radius
        cv2.circle(img, (coordinate[0], coordinate[1]), radius, color, thickness)
        cv2.putText(img, '%i' % i_cont, (coordinate[0] + 10, coordinate[1] - 10),
                    font, font_scale, color, fontthickness, cv2.LINE_AA)

    if showing_img:
        image_show(img)


def save_out_dict(data, file_name):
    '''

    :param dict:
    :param file_name:
    :return:
    '''
    json_dump = json.dumps(data, cls=NumpyEncoder)
    file_name = replce_format_from_file_name(file_name)
    pathlib.Path(file_name).write_text(json_dump, encoding="utf-8")


def path_abs_make(path_in):
    this_folder = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(this_folder, path_in)


def gaussian_blurring(img, k):
    # k = 3, 7, 11..
    img_blur = cv2.GaussianBlur(img, (k, k), 0)

    return img_blur
