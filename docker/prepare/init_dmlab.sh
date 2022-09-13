# E: Failed to fetch http://mirrors.aliyun.com/ubuntu/pool/main/libx/libxau/libxau6_1.0.8-1ubuntu1_amd64.deb  Temporary failure resolving 'mirrors.aliyun.com'
# E: Unable to fetch some archives, maybe run apt-get update or try with --fix-missing?

# python3 -m pip install --upgrade pip
PRE_PATH=`pwd`

pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple

apt-get update --fix-missing
apt-get install -y \
    curl \
    zip \
    unzip \
    software-properties-common \
    pkg-config \
    g++-4.8 \
    zlib1g-dev \
    lua5.1 \
    liblua5.1-0-dev \
    libffi-dev \
    gettext \
    freeglut3 \
    libsdl2-dev \
    libosmesa6-dev \
    libglu1-mesa \
    libglu1-mesa-dev \
    python3-dev \
    build-essential \
    git \
    python-setuptools \
    python3-pip \
    libjpeg-dev \
    tmux vim wget htop

# Build and install DeepMind Lab pip package.
# We explicitly set the Numpy path as shown here:
# https://github.com/deepmind/lab/blob/master/docs/users/build.md

NP_INC="$(python3 -c 'import numpy as np; print(np.get_include()[5:])')"

## if need compile ....
# unzip -q lab-937d53eecf7b46fbfc56c62e8fc2257862b907f2.zip
# mv lab-937d53eecf7b46fbfc56c62e8fc2257862b907f2 lab

#     # git clone https://github.com/deepmind/lab.git && \
# cd lab && \
#     # git checkout 937d53eecf7b46fbfc56c62e8fc2257862b907f2 && \
#     sed -i 's@python3.5@python3.6@g' python.BUILD && \
#     sed -i 's@glob(\[@glob(["'"$NP_INC"'/\*\*/*.h", @g' python.BUILD && \
#     sed -i 's@: \[@: ["'"$NP_INC"'", @g' python.BUILD && \
#     sed -i 's@650250979303a649e21f87b5ccd02672af1ea6954b911342ea491f351ceb7122@1e9793e1c6ba66e7e0b6e5fe7fd0f9e935cc697854d5737adec54d93e5b3f730@g' WORKSPACE && \
#     bazel build -c opt python/pip_package:build_pip_package --incompatible_remove_legacy_whole_archive=0 && \
#     pip3 install wheel && \
#     PYTHON_BIN_PATH="/usr/bin/python3" ./bazel-bin/python/pip_package/build_pip_package /tmp/dmlab_pkg && \
#     pip3 install /tmp/dmlab_pkg/DeepMind_Lab-*.whl --force-reinstall && \
#     # rm -rf /lab
## [END] if need compile ....
## [ELSE] if the whl is compiled ....
    rm lab-937d53eecf7b46fbfc56c62e8fc2257862b907f2.zip
    pip3 install wheel
    pip3 install ./DeepMind_Lab-*.whl --force-reinstall
## [END] if the whl is compiled ....

# Install dataset (from https://github.com/deepmind/lab/tree/master/data/brady_konkle_oliva2008)
mkdir /dataset && \
    cd /dataset && \
    pip3 install Pillow

# curl -sS https://raw.githubusercontent.com/deepmind/lab/master/data/brady_konkle_oliva2008/README.md | \
# tr '\n' '\r' | \
# sed -e 's/.*```sh\(.*\)```.*/\1/' | \
# tr '\r' '\n' | \
mv $PRE_PATH/ObjectsAll.zip .
bash $PRE_PATH/get_dmlab_data.sh

pip3 install gym dataclasses
pip3 install tensorflow_probability==0.11.0

# Copy SEED codebase and SEED GRPC binaries.
# ADD . /seed_rl/
# WORKDIR /seed_rl
# ENTRYPOINT ["python3", "gcp/run.py"]
