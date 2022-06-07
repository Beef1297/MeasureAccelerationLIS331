# Weight Kinesthesia 用の Utils
import numpy as np
import os

def save_csv(dir_path, numbering, data) :
    # ディレクトリパス を確認 (なかったら作成)
    if not os.path.isdir(dir_path) :
        os.makedirs(dir_path)
    file_path = os.path.join(dir_path, "acceleration-{0}.csv".format(numbering))
    # csv 書き出し
    # 毎計測秒 csv に書き出す.
    np.savetxt(file_path, data, delimiter=",", header="t,x,y,z", fmt="%.16f")
    return