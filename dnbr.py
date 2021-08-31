import sentinelsat
import rasterio
import numpy as np

class dNBR:
    def __init__(self):
        self.pre_img_paths = dict()
        self.post_img_paths = dict()

    def setPreSWIRPath(self, path):
        self.pre_img_paths["SWIR"] = path

    def setPreNIRPath(self, path):
        self.pre_img_paths["NIR"] = path

    def setPreSCLPath(self, path):
        self.pre_img_paths["SCL"] = path

    def setPostSWIRPath(self, path):
        self.post_img_paths["SWIR"] = path

    def setPostNIRPath(self, path):
        self.post_img_paths["NIR"] = path

    def setPostSCLPath(self, path):
        self.post_img_paths["SCL"] = path
    
    #Returns dNBR array, requires pre SWIR pre NIR post SWIR and post NIR paths.
    #If result_fname is given, then writes dNBR result to a tiff file named as result_fname.
    def calculate(self, result_fname=None, float_out=False):
        #Function for NBR calculation, arrays must be converted to int
        def calculateNBR(nir, swir):
            nir = nir.astype("int")
            swir = swir.astype("int")
            return (nir - swir) / (nir + swir)
        #Check if image paths are valid
        if not (self.pre_img_paths.get("NIR", 0) and self.pre_img_paths.get("SWIR", 0)
                and self.post_img_paths.get("NIR", 0) and self.post_img_paths.get("SWIR", 0)):
            print(  "Please first set necessary image paths using "
                    "setPreNIRPath, setPreSWIRPath, setPostNIRPath, setPostSWIRPath methods.")
            return np.zeros(1)
        #Open pre images with rasterio
        pre_fire_swir = rasterio.open(self.pre_img_paths["SWIR"])
        pre_fire_nir = rasterio.open(self.pre_img_paths["NIR"])
        #Check if SWIR and NIR images are compatible
        pre_width = pre_fire_swir.width if pre_fire_swir.width == pre_fire_nir.width else 0
        pre_height = pre_fire_swir.height if pre_fire_swir.height == pre_fire_nir.height else 0
        pre_crs = pre_fire_swir.crs if pre_fire_swir.crs == pre_fire_nir.crs else 0
        pre_transform = pre_fire_swir.transform if pre_fire_swir.transform == pre_fire_nir.transform else 0
        pre_dtype = pre_fire_swir.dtypes[0] if pre_fire_swir.dtypes[0] == pre_fire_nir.dtypes[0] else 0
        if ( pre_width and pre_height and pre_crs and pre_transform ) == 0:
            print("Properties of pre SWIR and NIR images are different")
            pre_fire_swir.close()
            pre_fire_nir.close()
            return np.zeros(1)
        #Calculate pre nbr then check and apply the SCL image (if there is one)
        pre_nbr = calculateNBR(pre_fire_nir.read(1), pre_fire_swir.read(1))
        if self.pre_img_paths.get("SCL", 0):
            pre_fire_scl = rasterio.open(self.pre_img_paths["SCL"])
            if ((pre_width == pre_fire_scl.width) and
                (pre_height == pre_fire_scl.height) and
                (pre_crs == pre_fire_scl.crs) and
                (pre_transform == pre_fire_scl.transform)):
                pre_fire_water_mask = ((pre_fire_scl.read(1) != 6) * 1).astype("uint8")
            pre_fire_scl.close()
        pre_fire_swir.close()
        pre_fire_nir.close()
        #Open post images with rasterio
        post_fire_swir = rasterio.open(self.post_img_paths["SWIR"])
        post_fire_nir = rasterio.open(self.post_img_paths["NIR"])
        #Check if SWIR and NIR images are compatible
        post_width = post_fire_swir.width if post_fire_swir.width == post_fire_nir.width else 0
        post_height = post_fire_swir.height if post_fire_swir.height == post_fire_nir.height else 0
        post_crs = post_fire_swir.crs if post_fire_swir.crs == post_fire_nir.crs else 0
        post_transform = post_fire_swir.transform if post_fire_swir.transform == post_fire_nir.transform else 0
        post_dtype = post_fire_swir.dtypes[0] if post_fire_swir.dtypes[0] == post_fire_nir.dtypes[0] else 0
        if ( post_width and post_height and post_crs and post_transform ) == 0:
            print("Properties of post SWIR and NIR images are different")
            post_fire_swir.close()
            post_fire_nir.close()
            return np.zeros(1)
        #Check if pre and post images are compatible
        if (    pre_width != post_width or
                pre_height != post_height or
                pre_crs != post_crs or
                pre_transform != post_transform or
                pre_dtype != post_dtype ):
            print("Properties of pre and post fire images are different")
            post_fire_swir.close()
            post_fire_nir.close()
            return np.zeros(1)
        #Calculate post nbr then check and apply the SCL image (if there is one)
        post_nbr = calculateNBR(post_fire_nir.read(1), post_fire_swir.read(1))
        if self.post_img_paths.get("SCL", 0):
            post_fire_scl = rasterio.open(self.post_img_paths["SCL"])
            if ((post_width == post_fire_scl.width) and
                (post_height == post_fire_scl.height) and
                (post_crs == post_fire_scl.crs) and
                (post_transform == post_fire_scl.transform)):
                post_fire_water_mask = ((post_fire_scl.read(1) != 6) * 1).astype("uint8")
            post_fire_scl.close()
        post_fire_swir.close()
        post_fire_nir.close()
        #Water mask calculation from pre and post SCL water mask data.
        #If there is no SCL being read before, then water mask will just array of 1s.
        water_mask = np.zeros_like(post_nbr, dtype="uint8")
        try:
            water_mask += post_fire_water_mask
            del post_fire_water_mask
        except NameError:
            pass
        try:
            water_mask += pre_fire_water_mask
            del pre_fire_water_mask
        except NameError:
            pass
        if water_mask.any():
            water_mask = (water_mask != 0) * 1
        else:
            water_mask += 1
        #Calculate difference of the pre and post nbr and apply water_mask
        dNBR_float = (pre_nbr - post_nbr) * water_mask
        del pre_nbr, post_nbr, water_mask
        #If float out is needed then return it otherwise char out will be calculated
        #Char out consist of classified version of the float dnbr.
        #In char array: 0 is regrowth high, 1 is regrowth low, 2 is unburned,
        #3 is low severity burn, 4 is moderate-low severity burn,
        #5 is miderate-high severity burn, 6 is high severity burn.
        if float_out:
            #Eliminate the nan
            for i in range(0, dNBR_float.shape[0]):
                for j in range(0, dNBR_float.shape[1]):
                    if dNBR_float[i][j] == np.nan:
                        dNBR_float[i][j] = 0
            #Write to file or just return the numpy array
            if result_fname:
                output = rasterio.open(result_fname, "w",width=pre_width,
                                                    height=pre_height,
                                                    count=1,
                                                    crs=pre_crs,
                                                    transform=pre_transform,
                                                    dtype=dNBR_float.dtype)
                output.write(dNBR_float, 1)
                output.close()
            return dNBR_float
        else:
            dNBR_char = np.zeros_like(dNBR_float, dtype="uint8")
            for i in range(0, dNBR_float.shape[0]):
                for j in range(0, dNBR_float.shape[1]):
                    if dNBR_float[i][j] == np.nan: #Unburned
                        dNBR_char[i][j] = 2
                    elif dNBR_float[i][j] < -0.25: #Regrowth high
                        dNBR_char[i][j] = 0
                    elif dNBR_float[i][j] < -0.1: #Regrowth low
                        dNBR_char[i][j] = 1
                    elif dNBR_float[i][j] < 0.1: #Unburned
                        dNBR_char[i][j] = 2
                    elif dNBR_float[i][j] < 0.27: #Low burn
                        dNBR_char[i][j] = 3
                    elif dNBR_float[i][j] < 0.44: #Moderate-low burn
                        dNBR_char[i][j] = 4
                    elif dNBR_float[i][j] < 0.66: #Miderate-high burn
                        dNBR_char[i][j] = 5
                    else: #High burn
                        dNBR_char[i][j] = 6
            del dNBR_float
            if result_fname:
                output = rasterio.open(result_fname, "w",width=pre_width,
                                                    height=pre_height,
                                                    count=1,
                                                    crs=pre_crs,
                                                    transform=pre_transform,
                                                    dtype=dNBR_char.dtype)
                output.write(dNBR_char, 1)
                output.close()
            return dNBR_char
    #---

    def fromSentinel2WithIdentifier(self, username, password, first_img_ident, second_img_ident, out_fname, float_out=False):
        #Check for the processing level of images, function works only with level-2A images.
        if ("MSIL2A" not in first_img_ident) or ("MSIL2A" not in second_img_ident):
            print("Please use images having processing level 2A.")
            return
        #API connection
        self.api = sentinelsat.SentinelAPI(username, password)
        #Getting first image
        first_img = self.api.query(identifier=first_img_ident, processinglevel="Level-2A")
        if not first_img:
            print(first_img_ident + " could not be found.")
            return
        first_img_id = list(first_img)[0]
        #Getting second image
        second_img = self.api.query(identifier=second_img_ident, processinglevel="Level-2A")
        if not second_img:
            print(second_img_ident + " could not be found.")
            return
        second_img_id = list(second_img)[0]
        if second_img[second_img_id]["ingestiondate"] > first_img[first_img_id]["ingestiondate"]:
            self.pre_img_id = first_img_id
            self.post_img_id = second_img_id
        elif second_img[second_img_id]["ingestiondate"] < first_img[first_img_id]["ingestiondate"]:
            self.post_img_id = first_img_id
            self.pre_img_id = second_img_id
        else:
            print("Image dates are same.")
            return
        #Node filters for different bandwidths
        b12_filter = sentinelsat.make_path_filter("*b12_20m.jp2")
        b8a_filter = sentinelsat.make_path_filter("*b8a_20m.jp2")
        scl_filter = sentinelsat.make_path_filter("*scl_20m.jp2")
        #Installing pre fire images and saving its absolute paths to pre_img_paths dict.
        temp_dict = self.api.download(self.pre_img_id, nodefilter=b12_filter)
        self.setPreSWIRPath(temp_dict["nodes"][list(temp_dict["nodes"].keys())[1]]["path"])
        temp_dict = self.api.download(self.pre_img_id, nodefilter=b8a_filter)
        self.setPreNIRPath(temp_dict["nodes"][list(temp_dict["nodes"].keys())[1]]["path"])
        temp_dict = self.api.download(self.pre_img_id, nodefilter=scl_filter)
        self.setPreSCLPath(temp_dict["nodes"][list(temp_dict["nodes"].keys())[1]]["path"])
        #Installing post fire images and saving its absolute paths to post_img_paths dict.
        temp_dict = self.api.download(self.post_img_id, nodefilter=b12_filter)
        self.setPostSWIRPath(temp_dict["nodes"][list(temp_dict["nodes"].keys())[1]]["path"])
        temp_dict = self.api.download(self.post_img_id, nodefilter=b8a_filter)
        self.setPostNIRPath(temp_dict["nodes"][list(temp_dict["nodes"].keys())[1]]["path"])
        temp_dict = self.api.download(self.post_img_id, nodefilter=scl_filter)
        self.setPostSCLPath(temp_dict["nodes"][list(temp_dict["nodes"].keys())[1]]["path"])
        del temp_dict
        #In error calculate method returns zero array.
        if not self.calculate(out_fname, float_out).any():
            print("dNBR could not be calculated from given images")
            return 1
        return 0

"""TODO
    def fromSentinel2WithLocation(location, fire_start, fire_end, out_fname):
        return 0
"""

if __name__ == "__main__":
    import sys
    dnbr = dNBR()
    try:
        dnbr.fromSentinel2WithIdentifier(   sys.argv[1],
                                            sys.argv[2],
                                            sys.argv[3],
                                            sys.argv[4],
                                            sys.argv[5],
                                            0)
    except IndexError:
        print("Basic usage: python dnbr.py 'username' 'password' 'img title 1' 'img title 2' 'out_file_name.tiff'")
