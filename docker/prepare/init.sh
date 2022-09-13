# Copyright 2019 The SEED Authors
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Update apt source
echo "Update apt source (aliyun)"
mv /etc/apt/sources.list /etc/apt/sources.list.old
cp sources.list /etc/apt/sources.list

# Update Nvidia Key
echo "Update Nvidia Key"
# ref: https://forums.developer.nvidia.com/t/notice-cuda-linux-repository-key-rotation/212772
# apt-get update
# apt-get install -y wget

apt-key del 7fa2af80

# apt-key del F60F4B3D7FA2AF80

rm /etc/apt/sources.list.d/cuda.list
rm /etc/apt/sources.list.d/nvidia-ml.list

# ref: https://github.com/NVIDIA/nvidia-docker/issues/1631
# wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-keyring_1.0-1_all.deb 
dpkg -i cuda-keyring_1.0-1_all.deb

# wget -qO - https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub | apt-key add -
# gpg --keyserver keyserver.ubuntu.com --recv A4B469963BF863CC
# gpg --export --armor A4B469963BF863CC | apt-key add -


# Start
echo "Install dependencies"
apt-get update && apt-get install -y \
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
    tmux vim wget 

# Install bazel
echo "deb [arch=amd64] http://storage.googleapis.com/bazel-apt stable jdk1.8" | \
    tee /etc/apt/sources.list.d/bazel.list && \
    # curl https://bazel.build/bazel-release.pub.gpg | \
    apt-key add bazel-release.pub.gpg && \
    apt-get update && apt-get install -y bazel
